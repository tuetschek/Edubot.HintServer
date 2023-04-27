from flask.json import JSONEncoder

from typing import Any, TypeVar, Type, Callable, Optional

TNumber = TypeVar("TNumber", int, float, bool)
T = TypeVar("T")


def tryParse(val: Any, type: Type[TNumber]) -> bool:
    try:
        parsed_value = type(val)
        return True
    except:
        return False


def getNumberFromDict(obj: dict, key: str, type: Type[TNumber]) -> Optional[TNumber]:
    return None if (key not in obj) or (not tryParse(obj[key], type)) else type(obj[key])


def getArrayFromDict(obj: dict, key: str, mappingFn: Callable[[Any], T] = lambda x: x) -> Optional[list[T]]:
    return None if (key not in obj) or (not isinstance(obj[key], list)) else list(map(mappingFn, obj[key]))


def getObjectFromDict(obj: dict, key: str, type: Type[T], mappingFn: Callable[[Any], T] = lambda x: None) -> Optional[T]:
    return None if (key not in obj) else obj[key] if isinstance(obj[key], type) else mappingFn(obj[key])


def mapObjectChildrenFromDict(obj: dict, key: str, mappingFn: Callable[[Any], T] = lambda x: x) -> Optional[T]:
    return None if (key not in obj) else mappingFn(obj[key])


def listOrEmpty(arr: Optional[list[T]]) -> list[T]:
    return [] if arr is None else arr

class ApiModel:
    def _addValuesFromDict(self, obj):
        pass

    def toJsonObject(self):
        return self.__dict__


class ApiModelJSONEncoder(JSONEncoder):
    def default(self, object):
        if isinstance(object, ApiModel):
            return object.toJsonObject()
        return super(JSONEncoder, self).default(object)


class SearchRequest(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.userId = getObjectFromDict(obj, "userId", str)
        self.query = getObjectFromDict(obj, "query", str)
        self.enumValues = getArrayFromDict(
            obj, "enumValues", lambda x: EnumList(x))
        self.startIndex = getNumberFromDict(obj, "startIndex", int)
        self.itemCount = getNumberFromDict(obj, "itemCount", int)
        self.detectEnums = getNumberFromDict(obj, "detectEnums", bool)
        self.returnSearchHints = getNumberFromDict(
            obj, "returnSearchHints", bool)
        self.returnWizardHints = getNumberFromDict(
            obj, "returnWizardHints", bool)
        self.returnDropdownValues = getNumberFromDict(
            obj, "returnDropdownValues", bool)
        self.doRedirection = getNumberFromDict(obj, "doRedirection", bool)
        self.useLemmatizer = getNumberFromDict(obj, "useLemmatizer", bool)


class SearchResponse(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.originalQuery = getObjectFromDict(obj, "originalQuery", str)
        self.startIndex = getNumberFromDict(obj, "startIndex", int)
        self.itemCount = getNumberFromDict(obj, "itemCount", int)
        self.totalCount = getNumberFromDict(obj, "totalCount", int)
        self.reducedQuery = getObjectFromDict(obj, "reducedQuery", str)
        self.enumValues = getArrayFromDict(
            obj, "enumValues", lambda x: EnumList(x))
        self.items = getArrayFromDict(
            obj, "items", lambda x: ResultItem(x))
        self.searchHints = getArrayFromDict(
            obj, "searchHints", lambda x: list(map(lambda y: EnumItem(y), x)))
        self.wizardHints = getObjectFromDict(
            obj, "wizardHints", EnumList, lambda x: EnumList(x))
        self.dropdownValues = getArrayFromDict(
            obj, "dropdownValues", lambda x: EnumCountList(x))
        self.redirectedFromReducedQuery = getObjectFromDict(
            obj, "redirectedFromReducedQuery", str)
        self.redirectedFromEnumValues = getArrayFromDict(
            obj, "redirectedFromEnumValues", lambda x: EnumList(x))


class EnumItem(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.id = getNumberFromDict(obj, "id", int)
        self.enumType = getObjectFromDict(obj, "enumType", str)
        self.valueCode = getObjectFromDict(obj, "valueCode", str)


class EnumList(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.enumType = getObjectFromDict(obj, "enumType", str)
        self.isNotRelevant = getNumberFromDict(obj, "isNotRelevant", bool)
        self.values = getArrayFromDict(
            obj, "values", lambda x: EnumListItem(x))


class EnumListItem(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.id = getNumberFromDict(obj, "id", int)
        self.valueCode = getObjectFromDict(obj, "valueCode", str)


class EnumCountList(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.enumType = getObjectFromDict(obj, "enumType", str)
        self.values = getArrayFromDict(
            obj, "values", lambda x: EnumCountListItem(x))


class EnumCountListItem(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.id = getNumberFromDict(obj, "id", int)
        self.valueCode = getObjectFromDict(obj, "valueCode", str)
        self.count = getNumberFromDict(obj, "count", int)


class ResultItem(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.id = getObjectFromDict(obj, "id", str)
        self.url = getObjectFromDict(obj, "url", str)
        self.title = getObjectFromDict(obj, "title", str)
        self.score = getNumberFromDict(obj, "score", float)


class HintRequest(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.textValue = getObjectFromDict(obj, "textValue", str)
        self.enumValues : Optional[dict[str,list[str]]] = getObjectFromDict(obj, "enumValues", dict)
        self.notRelevantValues = {key: True for key in listOrEmpty(
            getArrayFromDict(obj, "notRelevantValues", lambda x: str(x)))}


class HintResponse(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.wizardHints = getArrayFromDict(
            obj, "wizardHints", lambda x: WizardHint(x))
        self.searchHints = getArrayFromDict(
            obj, "searchHints", lambda x: SearchHint(x))


class WizardHint(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.field = getObjectFromDict(obj, "field", str)
        self.values = getArrayFromDict(obj, "values")


class SearchHint(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.fieldsAndValues = getObjectFromDict(obj, "fieldsAndValues", dict)


class RedirectRequest(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.detectEnums = getNumberFromDict(obj, "detectEnums", bool)
        self.doRedirection = getNumberFromDict(obj, "doRedirection", bool)
        self.textValue = getObjectFromDict(obj, "textValue", str)
        self.enumValues : Optional[dict[str, list[str]]] = getObjectFromDict(obj, "enumValues", dict)
        self.notRelevantValues : Optional[dict[str, bool]]  = {key: True for key in listOrEmpty(
            getArrayFromDict(obj, "notRelevantValues", lambda x: str(x)))}


class RedirectResponse(ApiModel):
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        ApiModel.__init__(self)
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.anyDetection = getNumberFromDict(obj, "anyDetection", bool)
        self.anyRedirection = getNumberFromDict(obj, "anyRedirection", bool)
        self.detectedTextValue = getObjectFromDict(obj, "detectedTextValue", str)
        self.detectedEnumValues : Optional[dict[str, list[str]]] = getObjectFromDict(obj, "detectedEnumValues", dict)
        self.detectedNotRelevantValues = getArrayFromDict(obj, "redirectedNotRelevantValues", lambda x: str(x))
        self.redirectedTextValue = getObjectFromDict(obj, "redirectedTextValue", str)
        self.redirectedEnumValues : Optional[dict[str, list[str]]] = getObjectFromDict(obj, "redirectedEnumValues", dict)
        self.redirectedNotRelevantValues = getArrayFromDict(obj, "redirectedNotRelevantValues", lambda x: str(x))


class AppConfiguration:
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.defaultConfiguration = getObjectFromDict(
            obj, "DefaultConfiguration", DefaultConfiguration, lambda x: DefaultConfiguration(x))
        self.collections = mapObjectChildrenFromDict(obj, "Collections", lambda x: { key: CollectionConfiguration(value) for key, value in x.items()})


class DefaultConfiguration:
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.defaultCollection = getObjectFromDict(
            obj, "DefaultCollection", str)


class CollectionConfiguration:
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.solrQueryUrlPattern = getObjectFromDict(
            obj, "SolrQueryUrlPattern", str)
        self.lemmatizeUrlPattern = getObjectFromDict(obj, "LemmatizeUrlPattern", str)
        self.idField = getObjectFromDict(obj, "IdField", str)
        self.searchField = getObjectFromDict(obj, "SearchField", str)
        self.wizardHintFields = getArrayFromDict(
            obj, "WizardHintFields", lambda x: x)
        self.searchHintFields = getArrayFromDict(
            obj, "SearchHintFields", lambda x: x)
        self.dropdownFields = getArrayFromDict(
            obj, "DropdownFields", lambda x: x)
        self.enumValues = getArrayFromDict(
            obj, "EnumValues", lambda x: CollectionConfigurationEnumValue(x))
        self.precomputedSolrUrlParams: Optional[str] = None
        self.precomputedValueCodeToValueText: Optional[dict[str, str]] = None
        self.precomputedValueFieldAndTextToValue: Optional[dict[(str, str), CollectionConfigurationEnumValue]] = None


class CollectionConfigurationEnumValue:
    def __init__(self, obj: Optional[dict[str, Any]] = None, **kwargs):
        obj = kwargs if obj is None else obj
        self._addValuesFromDict(obj)

    def _addValuesFromDict(self, obj: dict[str, Any]):
        self.id = getNumberFromDict(obj, "Id", int)
        self.code = getObjectFromDict(obj, "Code", str)
        self.text = getObjectFromDict(obj, "Text", str)
        self.field = getObjectFromDict(obj, "Field", str)
        self.isUnknown = getNumberFromDict(obj, "IsUnknown", bool)
        self.isNotRelevant = getNumberFromDict(obj, "IsNotRelevant", bool)


NotRelevantFields = dict[str, bool]
SolrResponse = dict
