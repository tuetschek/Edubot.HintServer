import json
import re
import logging
import copy
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
    originalRequest =  copy.copy(request) # store a copy of the original request if needed for backoff
    response = models.SearchResponse()
    response.originalQuery = request.query

    # Get collection
    defaultCollection = asNotNone(
        config.defaultConfiguration).defaultCollection
    collectionConfig = asNotNone(config.collections)[defaultCollection]
    hintingparams = getOrCreateSolrUrlParams(collectionConfig)

    # prepare lemmatized text if lemmatizer URL is non-empty
    lemmatized = lemmatize(collectionConfig.lemmatizeUrlPattern, request.query)
    request.lemmatizedQuery = lemmatized.lemmatized

    # Conditionally redirect
    redirectResponse = None
    if request.detectEnums is True or request.doRedirection is True:
        redirectRequest = mapSearchRequestToRedirectRequest(request, lemmatized, collectionConfig)
        redirectResponse = redirect(redirectRequest, collectionConfig)

        if redirectResponse.anyDetection or redirectResponse.anyRedirection:
            response.originalQuery = request.query
            response.redirectedFromReducedQuery = None  # XXX not sure why this isn't actually used
            response.redirectedFromEnumValues = []
            request = addRedirectToResponse(request, redirectResponse, collectionConfig)

    # Add redirected values to response
    if response.originalQuery is None:
        response.originalQuery = request.query
    response.reducedQuery = request.query
    response.enumValues = request.enumValues

    # Preprocess
    evCode2Text = getOrCreateValueCodeToTextMapping(collectionConfig)

    enumValues = {ev.enumType: [evCode2Text[value.valueCode]
                                for value in ev.values]
                  for ev in ([] if request.enumValues is None else request.enumValues)
                  if not ev.isNotRelevant}
    notRelevantFields = {asNotNone(item.enumType): True
                         for item in request.enumValues
                         if item.isNotRelevant}

    # Generate URL for Solr
    url = formatUrl(collectionConfig.solrQueryUrlPattern, request.query, request.lemmatizedQuery,
                    hintingparams, enumValues, notRelevantFields)

    # Call Solr
    connection = urlopen(url)
    solrResponse = json.load(connection)

    # If we made enum detection and then didn't find anything, back off & do search w/o detection, using the orig. request
    if int(solrResponse["response"]["numFound"]) == 0 and redirectResponse is not None and redirectResponse.anyDetection:
        originalRequest.detectEnums = False
        return search(originalRequest, config)

    # Generate hints
    if request.returnSearchHints is True:
        candidates = generateSearchHints(enumValues, notRelevantFields, solrResponse, collectionConfig)
        response.searchHints = [downgradeSearchHint2EnumItem(x, collectionConfig) for x in candidates]
    else:
        response.searchHints = None

    if request.returnWizardHints is True:
        candidates = generateWizardHints(enumValues, notRelevantFields, solrResponse, collectionConfig)
        if len(candidates) > 0:
            response.wizardHints = downgradeWizardHint2EnumList(candidates[0], collectionConfig)
    else:
        response.wizardHints = None

    # Not implemented
    response.startIndex = 0
    response.itemCount = int(solrResponse["response"]["numFound"])
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


def redirect(request: models.RedirectRequest, config: models.CollectionConfiguration) -> models.RedirectResponse:
    response = models.RedirectResponse()
    evCode2Val = getOrCreateValueCodeToValueMapping(config)

    matches = [(kw, kw.regex.search(request.lemmatized.lemmatized)) for kw in config.keywords if kw.isDetected and kw.regex]
    enum_matches = [(kw, m) for kw, m in matches if m and kw.enumValueCode]

    # Detect
    if request.detectEnums is True and enum_matches:
        # remove any matches that have enumValueCode from both plain and lemmatized text
        enum_matches.sort(reverse=True, key=lambda i: i[1].start())
        reduced_text = request.lemmatized.plain
        reduced_lemmas = request.lemmatized.lemmatized
        enum_ret = []
        # XXX if redirection is needed, we'd need to work with alignment as well here (& recompute everything properly)
        for kw, m in enum_matches:
            reduced_text = reduced_text[:request.lemmatized.mapIndex(m.start())] + reduced_text[request.lemmatized.mapIndex(m.end()):]
            reduced_lemmas = reduced_lemmas[:m.start()] + reduced_lemmas[m.end():]
            enum_ret.append(evCode2Val.get(kw.enumValueCode))
        # set resulting values
        response.anyDetection = True
        response.detectedTextValue = reduced_text.replace('  ', ' ').strip()
        response.detectedLemmatizedValue = reduced_lemmas.replace('  ', ' ').strip()
        response.detectedEnumValues = enum_ret
        response.detectedNotRelevantValues = [field for field in request.notRelevantValues]
    else:
        response.anyDetection = False
        response.detectedTextValue = request.textValue
        response.detectedLemmatizedValue = request.lemmatized.lemmatized
        response.detectedEnumValues = request.enumValues
        response.detectedNotRelevantValues = [field for field in request.notRelevantValues]

    # Redirect
    if request.doRedirection is True:
        pass  # TODO
    else:
        response.anyRedirection = False
        response.redirectedTextValue = response.detectedTextValue
        response.redirectedEnumValues = response.detectedEnumValues
        response.redirectedLemmatizedValue = response.detectedLemmatizedValue
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


def getOrCreateValueCodeToValueMapping(collectionConfig: models.CollectionConfiguration) -> dict[(str, str), models.CollectionConfigurationEnumValue]:
    if collectionConfig.precomputedValueCodeToValue is not None:
        return collectionConfig.precomputedValueCodeToValue

    mapping = {asNotNone(ev.code): ev for ev in collectionConfig.enumValues}
    collectionConfig.precomputedValueCodeToValue = mapping

    return mapping


def mapSearchRequestToRedirectRequest(searchRequest: models.SearchRequest, lemmatized: models.LemmatizedString, collectionConfig: models.CollectionConfiguration) -> models.RedirectRequest:
    evCode2Text = getOrCreateValueCodeToTextMapping(collectionConfig)

    req = models.RedirectRequest()
    req.detectEnums = searchRequest.detectEnums
    req.doRedirection = searchRequest.doRedirection
    req.textValue = searchRequest.query
    req.lemmatized = lemmatized
    req.enumValues = {enumList.enumType: [evCode2Text[
        enumListItem.valueCode] for enumListItem in enumList.values] for enumList in searchRequest.enumValues}
    req.notRelevantValues = [asNotNone(
        item.enumType) for item in searchRequest.enumValues if item.isNotRelevant]

    return req


def addRedirectToResponse(oldSearchRequest: models.SearchRequest, redirectResponse: models.RedirectResponse, collectionConfig: models.CollectionConfiguration) -> models.SearchRequest:

    req = models.SearchRequest()
    req.detectEnums = oldSearchRequest.detectEnums
    req.doRedirection = oldSearchRequest.doRedirection
    req.returnSearchHints = oldSearchRequest.returnSearchHints
    req.returnWizardHints = oldSearchRequest.returnWizardHints
    req.enumValues: list[models.EnumList] = []
    req.query = redirectResponse.detectedTextValue
    req.lemmatizedQuery = redirectResponse.detectedLemmatizedValue

    # group detected enum values by field
    fieldVals = {}
    for val in asNotNone(redirectResponse.detectedEnumValues):
        fieldVals[val.field] = fieldVals.get(val.field, [])
        fieldVals[val.field].append(val)

    # add the enum values in the correct format
    for field, values in fieldVals.items():
        enumList = models.EnumList()
        enumList.isNotRelevant = False
        enumList.enumType = field
        enumList.values: list[models.EnumListItem] = []
        for value in values:
            enumListItem = models.EnumListItem()
            enumListItem.id = value.id
            enumListItem.valueCode = value.code
            enumList.values.append(enumListItem)
        req.enumValues.append(enumList)

    for field in asNotNone(redirectResponse.detectedNotRelevantValues):
        enumList = models.EnumList()
        enumList.isNotRelevant = True
        enumList.enumType = field
        req.enumValues.append(field)

    return req


def lemmatize(urlPattern: str, text: str):
    """Lemmatize using Morphodita API, if URL is set up; produce alignment between original and lemmatized"""
    if urlPattern:
        # get the lemmatized version
        url = urlPattern.replace("{text}", quote(text))
        connection = urlopen(url)
        response = json.load(connection)
        # compute alignment
        lemmatized = ''
        alignment = [(0, 0)]
        plain_pos = 0
        for tok in [tok for sent in response['result'] for tok in sent]:
            space = tok.get('space', '')
            lemmatized = lemmatized + tok['lemma'] + space
            plain_pos += len(tok['token']) + len(space)
            alignment.append((len(lemmatized), plain_pos))
        return models.LemmatizedString(plain=text, lemmatized=lemmatized, alignment=alignment)
    else:
        # backoff to no lemmatization
        return models.LemmatizedString(plain=text, lemmatized=text)


def formatUrl(urlPattern: Optional[str],
              text: Optional[str], lemmatizedText: Optional[str],
              hintingParams: Optional[str], enumValues: Optional[dict[str, list[str]]],
              notRelevantFields: Optional[dict[str, bool]]) -> str:

    urlPattern, text, hintingParams, enumValues, notRelevantFields = defaultIfNone(urlPattern, ""), defaultIfNone(text, ""), defaultIfNone(hintingParams, ""), defaultIfNone(enumValues, {}), defaultIfNone(notRelevantFields, {})

    # default lemmatized to plain text, if not available
    lemmatized_text = defaultIfNone(lemmatizedText, text)

    repls = list(re.finditer(r'(\\*)(\{[^\}]*\})', urlPattern))

    offset = 0
    url = ''
    for repl in repls:
        backslashes = repl.group(1)
        repl_start = repl.start() + len(backslashes)
        url += urlPattern[offset:repl_start]
        offset = repl.end()
        if len(backslashes) % 2:  # odd number of backslashes -- escaped, skip
            url += urlPattern[repl_start:offset]
            continue
        # Replace known mark-ups
        patternMatch = repl.group(2)
        if patternMatch == "{hintingparams}":
            url += hintingParams
        elif patternMatch == "{text|unquoted}":
            url += quote(text)
        elif patternMatch == "{text|quoted}":
            url += quote(f"\"{text}\"")
        elif patternMatch == "{text|lemmatized,unquoted}":
            url += quote(lemmatized_text)
        elif patternMatch == "{text|lemmatized,quoted}":
            url += quote(f"\"{lemmatized_text}\"")
        elif patternMatch.startswith("{enum:"):
            args = patternMatch[len("{enum:"):-1].split("|")
            if len(args) != 3 or args[1] != "convertFromId" or args[2] != "pre-AND":
                raise Exception(f"Invalid format of Solr query URL: Unsupported markup: {patternMatch}")
            enumField = args[0]
            if enumField not in enumValues or len(enumValues[enumField]) == 0 or enumField in notRelevantFields:
                pass
            else:
                enumValuesSeparated = " OR ".join(map(lambda x: f"({enumField}:\"{x}\")", enumValues[enumField]))
                url += quote(f" AND ({enumValuesSeparated})")
        else:
            raise Exception(f"Invalid format of Solr query URL: Unsupported markup: {patternMatch}")

    url += urlPattern[offset:]

    url = re.sub(r'\\([\\\{\}])', r'\1', url)  # unescape \, {, }
    url = url.replace(" ", "%20")

    logging.debug(url)
    return url
