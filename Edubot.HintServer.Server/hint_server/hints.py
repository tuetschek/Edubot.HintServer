from typing import Any

from hint_server.models import NotRelevantFields, SolrResponse, CollectionConfiguration, SearchHint, WizardHint


def generateSearchHints(notRelevantFields: NotRelevantFields, solrResponse: SolrResponse, collectionConfig: CollectionConfiguration) -> list[SearchHint]:
    # TODO: IsUnknown, IsNotRelevant
    idField = collectionConfig.idField

    totalFound = int(solrResponse["response"]["numFound"])
    facetObj = solrResponse["stats"]["stats_fields"][idField]["facets"]

    candidates = []

    for field in facetObj:
        if field in notRelevantFields:
            continue

        fieldObj = facetObj[field]

        for fieldValue in fieldObj:
            score = fieldObj[fieldValue]["count"]
            candidates.append((field, fieldValue, score))

    candidates = sorted(
        candidates, key=lambda item: item[2], reverse=True)[0:5]

    return list(map(lambda c: SearchHint(fieldsAndValues={c[0]: c[1]}), candidates))


def generateWizardHints(notRelevantFields: dict[str, bool], solrResponse: dict[str, Any], collectionConfig: CollectionConfiguration) -> list[WizardHint]:
    # TODO: IsUnknown, IsNotRelevant
    idField = collectionConfig.idField

    totalFound = int(solrResponse["response"]["numFound"])
    facetObj = solrResponse["stats"]["stats_fields"][idField]["facets"]

    candidates = []

    for field in facetObj:
        if field in notRelevantFields:
            continue

        fieldObj = facetObj[field]

        sumx = sum(fieldValueObj["count"]
                   for fieldValue, fieldValueObj in fieldObj.items())
        sumxx = sum(fieldValueObj["count"] ** 2 for fieldValue,
                    fieldValueObj in fieldObj.items())

        if sumx == 0:
            continue

        score = sumxx + (totalFound - sumx) ** 2

        fieldValues = sorted(
            fieldObj, key=lambda fieldValue: fieldObj[fieldValue]["count"], reverse=True)
        candidates.append((field, fieldValues, score))

    candidates = sorted(candidates, key=lambda item: item[2])

    return list(map(lambda item: WizardHint(field=item[0], values=item[1]), candidates))
