import json
from urllib.request import urlopen
from typing import Any, TypeVar, Optional

import hint_server.models as models
from hint_server.model_mapping import downgradeSearchHint2EnumItem, downgradeWizardHint2EnumList
from hint_server.hints import generateSearchHints, generateWizardHints

T = TypeVar("T")


def asNotNone(value: Optional[T]) -> T:
    assert value is not None
    return value


def search(request: models.SearchRequest, config: models.AppConfiguration) -> models.SearchResponse:
    # Get collection
    defaultCollection = asNotNone(
        config.defaultConfiguration).defaultCollection
    collectionConfig = asNotNone(config.collections)[defaultCollection]
    hintingparams = getOrCreateSolrUrlParams(collectionConfig)

    # Preprocess
    if request.enumValues is None:
        request.enumValues = []
    notRelevantFields = {asNotNone(item.enumType): True for item in filter(
        lambda enumItem: enumItem.isNotRelevant, request.enumValues)}

    # Generate URL for Solr
    url = str.format(asNotNone(collectionConfig.solrQueryUrlPattern),
                     textUnquoted=request.query, hintingparams=hintingparams).replace(" ", "%20")

    # Call Solr
    connection = urlopen(url)
    solrResponse = json.load(connection)

    # Generate response with additional data
    searchResponse = models.SearchResponse()

    if request.returnSearchHints == True:
        candidates = generateSearchHints(
            notRelevantFields, solrResponse, collectionConfig)
        searchResponse.searchHints = list(
            map(lambda x: downgradeSearchHint2EnumItem(x, collectionConfig), candidates))

    if request.returnWizardHints == True:
        candidates = generateWizardHints(
            notRelevantFields, solrResponse, collectionConfig)
        if len(candidates) > 0:
            searchResponse.wizardHints = downgradeWizardHint2EnumList(
                candidates[0], collectionConfig)

    return searchResponse


def hint(request: models.HintRequest, config: models.AppConfiguration) -> models.HintResponse:
    # Get collection
    defaultCollection = asNotNone(
        config.defaultConfiguration).defaultCollection
    collectionConfig = asNotNone(config.collections)[defaultCollection]
    hintingparams = getOrCreateSolrUrlParams(collectionConfig)

    # Preprocess
    notRelevantFields = request.notRelevantValues

    # Generate URL for Solr
    url = str.format(asNotNone(collectionConfig.solrQueryUrlPattern),
                     textUnquoted=request.textValue, hintingparams=hintingparams).replace(" ", "%20")

    # Call Solr
    connection = urlopen(url)
    solrResponse = json.load(connection)

    # Generate response with additional data
    hintResponse = models.HintResponse()
    hintResponse.searchHints = generateSearchHints(
        notRelevantFields, solrResponse, collectionConfig)
    hintResponse.wizardHints = generateWizardHints(
        notRelevantFields, solrResponse, collectionConfig)

    return hintResponse


def redirect(request: models.SearchRequest, config: dict) -> None:
    return None


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
