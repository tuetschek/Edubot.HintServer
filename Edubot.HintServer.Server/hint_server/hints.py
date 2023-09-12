from typing import Optional
from hint_server.models import NotRelevantFields, SolrResponse, CollectionConfiguration, SearchHint, WizardHint


def generateSearchHints(enumValues: Optional[dict[str, list[str]]], notRelevantFields: NotRelevantFields, solrResponse: SolrResponse, collectionConfig: CollectionConfiguration) -> list[SearchHint]:
    # TODO: IsUnknown, IsNotRelevant
    idField = collectionConfig.idField

    specifiedFields = {}
    for field in notRelevantFields:
        specifiedFields[field] = True
    for field in (enumValues if enumValues is not None else {}):
        if len(enumValues[field]) > 0:
            specifiedFields[field] = True

    totalFound = int(solrResponse["response"]["numFound"])
    facetObj = solrResponse["stats"]["stats_fields"][idField]["facets"]
    candidates = []
    unkIrrVals = getOrCreateUnkIrrVals(collectionConfig)

    for field in facetObj:
        if field in specifiedFields or field not in collectionConfig.searchHintFields:
            continue

        fieldObj = facetObj[field]

        for fieldValue in fieldObj:
            if not fieldValue or (field, fieldValue) in unkIrrVals:
                continue
            count = int(fieldObj[fieldValue]["count"])
            score = (count ** 2) + ((totalFound - count) ** 2)
            candidates.append((field, fieldValue, -score))

    candidates = sorted(
        candidates, key=lambda item: item[2], reverse=True)[0:5]

    return list(map(lambda c: SearchHint(fieldsAndValues={c[0]: c[1]}), candidates))


def getOrCreateUnkIrrVals(collectionConfig: CollectionConfiguration) -> set[(str, str)]:
    """Pick out values marked as unknown or irrelevant from the enum values list, so we can ignore them in hints."""
    if collectionConfig.precomputedUnkIrrVals is not None:
        return collectionConfig.precomputedUnkIrrVals

    unkIrrSet = set()
    for ev in collectionConfig.enumValues:
        if ev.isUnknown or ev.isNotRelevant:
            unkIrrSet.add((ev.field, getattr(ev, collectionConfig.searchField)))

    collectionConfig.precomputedUnkIrrVals = unkIrrSet
    return unkIrrSet


def generateWizardHints(enumValues: Optional[dict[str, list[str]]], notRelevantFields: NotRelevantFields, solrResponse: SolrResponse, collectionConfig: CollectionConfiguration) -> list[WizardHint]:
    # TODO: IsUnknown, IsNotRelevant
    idField = collectionConfig.idField

    specifiedFields = {}
    for field in notRelevantFields:
        specifiedFields[field] = True
    for field in (enumValues if enumValues is not None else {}):
        if len(enumValues[field]) > 0:
            specifiedFields[field] = True

    totalFound = int(solrResponse["response"]["numFound"])
    facetObj = solrResponse["stats"]["stats_fields"][idField]["facets"]
    candidates = []
    unkIrrVals = getOrCreateUnkIrrVals(collectionConfig)

    for field in facetObj:
        if field in specifiedFields or field not in collectionConfig.wizardHintFields:
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

        # remove empty & irrelevant & unknown values
        fieldValues = [fieldValue for fieldValue in fieldValues if fieldValue and (field, fieldValue) not in unkIrrVals]

        # skip if we have nothing left, or the only value is set for *all* results, so it doesn't help disambiguate
        if not fieldValues or len(fieldValues) == 1 and fieldObj[fieldValues[0]]["count"] == totalFound:
            continue

        candidates.append((field, fieldValues, score))

    candidates = sorted(candidates, key=lambda item: item[2])

    return list(map(lambda item: WizardHint(field=item[0], values=item[1]), candidates))
