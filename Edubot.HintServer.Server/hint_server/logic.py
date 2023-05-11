import json
import re
import logging
from urllib.request import urlopen
from urllib.parse import quote
from typing import TypeVar, Optional

import hint_server.models as models
from hint_server.model_mapping import downgradeSearchHint2EnumItem, downgradeWizardHint2EnumList
from hint_server.hints import generateSearchHints, generateWizardHints

T = TypeVar("T")



def asNotNone(value: Optional[T]) -> T:
    assert value is not None
    return value
def defaultIfNone(value: Optional[T], defaultValue: T) -> T:
    return defaultValue if value is None else value


def search(request: models.SearchRequest, config: models.AppConfiguration) -> models.SearchResponse:
    response = models.SearchResponse()
    response.originalQuery = request.query

    # Get collection
    defaultCollection = asNotNone(
        config.defaultConfiguration).defaultCollection
    collectionConfig = asNotNone(config.collections)[defaultCollection]
    hintingparams = getOrCreateSolrUrlParams(collectionConfig)

    # Conditionally redirect
    if False:
        if request.detectEnums == True or request.doRedirection == True:
            redirectRequest = mapSearchRequestToRedirectRequest(
                request, collectionConfig)
            redirectResponse = redirect(redirectRequest, config)

            if redirectResponse.anyDetection or redirectResponse.anyRedirection:
                response.originalQuery = request.query
                response.redirectedFromReducedQuery = redirectResponse.detectedTextValue
                response.redirectedFromEnumValues = redirectResponse.detectedEnumValues
                request = combineRedirectResponseAndOldSearchRequestToRedirectedSearchRequest(
                    request, redirectResponse, collectionConfig)

    # Add redirected values to response
    if response.originalQuery is None:
        response.originalQuery = request.query
    response.reducedQuery = request.query
    response.enumValues = request.enumValues

    # Preprocess
    evCode2Text = getOrCreateValueCodeToTextMapping(collectionConfig)

    enumValues = {ev.enumType: [evCode2Text[value.valueCode] for value in ev.values] for ev in (
        [] if request.enumValues is None else request.enumValues) if not ev.isNotRelevant}
    notRelevantFields = {asNotNone(
        item.enumType): True for item in request.enumValues if item.isNotRelevant}

    # Generate URL for Solr
    url = formatUrl(collectionConfig.solrQueryUrlPattern, collectionConfig.lemmatizeUrlPattern,
                    request.query, hintingparams, enumValues, notRelevantFields)

    # Call Solr
    connection = urlopen(url)
    solrResponse = json.load(connection)

    # Generate hints
    if request.returnSearchHints == True:
        candidates = generateSearchHints(
            enumValues, notRelevantFields, solrResponse, collectionConfig)
        response.searchHints = [downgradeSearchHint2EnumItem(
            x, collectionConfig) for x in candidates]
    else:
        response.searchHints = None

    if request.returnWizardHints == True:
        candidates = generateWizardHints(
            enumValues, notRelevantFields, solrResponse, collectionConfig)
        if len(candidates) > 0:
            response.wizardHints = downgradeWizardHint2EnumList(
                candidates[0], collectionConfig)
    else:
        response.wizardHints = None

    # Not implemented
    response.startIndex = 0
    response.itemCount = 0
    response.items: list[models.ResultItem] = []
    response.totalCount = 0
    response.dropdownValues: list[models.EnumCountList] = []

    return response


def hint(request: models.HintRequest, config: models.AppConfiguration) -> models.HintResponse:
    # Get collection
    defaultCollection = asNotNone(
        config.defaultConfiguration).defaultCollection
    collectionConfig = asNotNone(config.collections)[defaultCollection]
    hintingparams = getOrCreateSolrUrlParams(collectionConfig)

    # Preprocess
    enumValues = request.enumValues
    notRelevantFields = request.notRelevantValues

    # Generate URL for Solr
    url = formatUrl(collectionConfig.solrQueryUrlPattern, request.textValue, hintingparams, enumValues, notRelevantFields)

    # Call Solr
    connection = urlopen(url)
    solrResponse = json.load(connection)

    # Generate response with additional data
    hintResponse = models.HintResponse()
    hintResponse.searchHints = generateSearchHints(
        enumValues, notRelevantFields, solrResponse, collectionConfig)
    hintResponse.wizardHints = generateWizardHints(
        enumValues, notRelevantFields, solrResponse, collectionConfig)

    return hintResponse


def redirect(request: models.RedirectRequest, config: dict) -> models.RedirectResponse:
    response = models.RedirectResponse()

    # Detect
    if request.detectEnums == True:
        pass # TODO
    else:
        response.anyDetection = False
        response.detectedTextValue = request.textValue
        response.detectedEnumValues = request.enumValues
        response.detectedNotRelevantValues = [field for field in request.notRelevantValues]

    # Redirect
    if request.doRedirection == True:
        pass # TODO
    else:
        response.anyRedirection = False
        response.redirectedTextValue = response.detectedTextValue
        response.redirectedEnumValues = response.detectedEnumValues
        response.redirectedNotRelevantValues = response.redirectedNotRelevantValues

    return response


def getOrCreateSolrUrlParams(collectionConfig: models.CollectionConfiguration) -> str:
    if collectionConfig.precomputedSolrUrlParams is not None:
        return collectionConfig.precomputedSolrUrlParams

    solrUrlQueryStatsArray = ["stats=true"]

    facetingFields = {}
    for field in asNotNone(collectionConfig.wizardHintFields):
        facetingFields[field] = True
    for field in asNotNone(collectionConfig.searchHintFields):
        facetingFields[field] = True
    for field in asNotNone(collectionConfig.dropdownFields):
        facetingFields[field] = True
    for field in facetingFields:
        solrUrlQueryStatsArray.append(f"stats.facet={field}")

    idField = asNotNone(collectionConfig).idField
    solrUrlQueryStatsArray.append(f"stats.field={idField}")

    solrUrlQueryStats = "&".join(solrUrlQueryStatsArray)
    collectionConfig.precomputedSolrUrlParams = solrUrlQueryStats
    return solrUrlQueryStats


def getOrCreateValueCodeToTextMapping(collectionConfig: models.CollectionConfiguration) -> dict[str, str]:
    if collectionConfig.precomputedValueCodeToValueText is not None:
        return collectionConfig.precomputedValueCodeToValueText

    mapping = {asNotNone(ev.code): asNotNone(getattr(ev, collectionConfig.searchField))
               for ev in collectionConfig.enumValues}
    collectionConfig.precomputedValueCodeToValueText = mapping

    return mapping


def getOrCreateValueFieldAndTextToValue(collectionConfig: models.CollectionConfiguration) -> dict[(str, str), models.CollectionConfigurationEnumValue]:
    if collectionConfig.precomputedValueFieldAndTextToValue is not None:
        return collectionConfig.precomputedValueFieldAndTextToValue

    mapping = {(asNotNone(ev.field), asNotNone(ev.text))
                : ev for ev in collectionConfig.enumValues}
    collectionConfig.precomputedValueFieldAndTextToValue = mapping

    return mapping


def mapSearchRequestToRedirectRequest(searchRequest: models.SearchRequest, collectionConfig: models.CollectionConfiguration) -> models.RedirectRequest:
    evCode2Text = getOrCreateValueCodeToTextMapping(collectionConfig)

    req = models.RedirectRequest()
    req.detectEnums = searchRequest.detectEnums
    req.doRedirection = searchRequest.doRedirection
    req.textValue = searchRequest.query
    req.enumValues = {enumList.enumType: [evCode2Text[
        enumListItem.valueCode] for enumListItem in enumList.values] for enumList in searchRequest.enumValues}
    req.notRelevantValues = [asNotNone(
        item.enumType) for item in searchRequest.enumValues if item.isNotRelevant]

    return req


def combineRedirectResponseAndOldSearchRequestToRedirectedSearchRequest(oldSearchRequest: models.SearchRequest, redirectResponse: models.RedirectResponse, collectionConfig: models.CollectionConfiguration) -> models.SearchRequest:
    evFieldText2EnumValue = getOrCreateValueFieldAndTextToValue(
        collectionConfig)

    req = models.SearchRequest()
    req.detectEnums = oldSearchRequest.detectEnums
    req.doRedirection = oldSearchRequest.doRedirection
    req.enumValues: list[models.EnumList] = []

    for field, values in asNotNone(redirectResponse.enumValues).items():
        enumList = models.EnumList()
        enumList.isNotRelevant = False
        enumList.enumType = field
        enumList.values: list[models.EnumListItem] = []
        for value in values:
            mappedEnumValue = evFieldText2EnumValue[(field, value)]
            enumListItem = models.EnumListItem()
            enumListItem.id = mappedEnumValue.id
            enumListItem.valueCode = mappedEnumValue.code
            enumList.values.append(enumListItem)
        req.enumValues.append(enumList)

    for field in asNotNone(redirectResponse.notRelevantValues):
        enumList = models.EnumList()
        enumList.isNotRelevant = True
        enumList.enumType = field
        req.enumValues.append(field)

    return req


def lemmatize(urlPattern: str, text: str):
    """Lemmatize using Morphodita API"""
    url = urlPattern.replace("{text}", text)
    connection = urlopen(url)
    response = json.load(connection)
    return ' '.join([tok['lemma'] for sent in response['result'] for tok in sent])


def formatUrl(urlPattern: Optional[str], lemmatizeUrlPattern: Optional[str],
              text: Optional[str], hintingParams: Optional[str], enumValues: Optional[dict[str,list[str]]],
              notRelevantFields: Optional[dict[str,bool]]) -> str:

    urlPattern, text, hintingParams, enumValues, notRelevantFields = defaultIfNone(urlPattern,""), defaultIfNone(text, ""), defaultIfNone(hintingParams, ""), defaultIfNone(enumValues, {}), defaultIfNone(notRelevantFields, {})

    patternRegex = re.compile(r"^[^\}]*(?<!\\)(\{[^\}]*\}).*$")  # neg. lookbehind -- avoid escaped {

    # prepare lemmatized text if lemmatizer URL is non-empty
    lemmatized_text = lemmatize(lemmatizeUrlPattern, text) if lemmatizeUrlPattern else text

    # Start with non-replaced pattern
    url = urlPattern

    while True:
        # Get another match
        patternMatch = patternRegex.match(url)
        if patternMatch is None: break
        # Replace known mark-ups
        patternMatch = patternMatch.group(1)
        if patternMatch == "{hintingparams}":
            url = url.replace(patternMatch, hintingParams)
        elif patternMatch == "{text|unquoted}":
            url = url.replace(patternMatch, quote(text))
        elif patternMatch == "{text|quoted}":
            url = url.replace(patternMatch, quote(f"\"{text}\""))
        elif patternMatch == "{text|lemmatized,unquoted}":
            url = url.replace(patternMatch, quote(lemmatized_text))
        elif patternMatch == "{text|lemmatized,quoted}":
            url = url.replace(patternMatch, quote(f"\"{lemmatized_text}\""))
        elif patternMatch.startswith("{enum:"):
            args = patternMatch[len("{enum:"):-1].split("|")
            if len(args) != 3 or args[1] != "convertFromId" or args[2] != "pre-AND":
                raise Exception(f"Invalid format of Solr query URL: Unsupported markup: {patternMatch}")
            enumField = args[0]
            if enumField not in enumValues or len(enumValues[enumField]) == 0 or enumField in notRelevantFields:
                url = url.replace(patternMatch, "")
            else:
                enumValuesSeparated = " OR ".join(map(lambda x: f"({enumField}:\"{x}\")", enumValues[enumField]))
                url = url.replace(patternMatch, quote(f" AND ({enumValuesSeparated})"))
        else:
            raise Exception(f"Invalid format of Solr query URL: Unsupported markup: {patternMatch}")

    url = re.sub(r'\\([\\\{\}])', r'\1', url)  # unescape \, {, }
    url = url.replace(" ", "%20")

    logging.debug(url)
    return url
