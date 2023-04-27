import json
from typing import Any

from hint_server.models import AppConfiguration

config = None
error_description = None

def readAndValidateConfig(path: str):
    global config
    global error_description

    def isNone(value: Any, path: str) -> bool:
        global config
        global error_description
        if value is None:
            config = None
            error_description = f"Element {path} is missing or has invalid format"
            return True
        return False


    with open(path, "r", encoding="utf8") as file:
        try:
            config = json.load(file)
        except Exception as ex:
            config = None
            error_description = f"Config file is not a valid JSON: {ex}"
            return

    if config is None:
        error_description = f"Config file is not a valid JSON"
        return

    config = AppConfiguration(config)

    if isNone(config.defaultConfiguration, "root/DefaultConfiguration"): return
    if isNone(config.collections, "root/Collections"): return

    assert config.collections is not None
    for collectionName, collectionObj in config.collections.items():
        collectionPath = f"root/Collections/{collectionName}"
        enumValuePath = f"{collectionPath}/EnumValues"

        if isNone(collectionObj.solrQueryUrlPattern, collectionPath + "/SolrQueryUrlPattern"): return
        if isNone(collectionObj.lemmatizeUrlPattern, collectionPath + "/LemmatizeUrlPattern"): return
        if isNone(collectionObj.idField, collectionPath + "/IdField"): return
        if isNone(collectionObj.searchField, collectionPath + "/SearchField"): return
        if isNone(collectionObj.wizardHintFields, collectionPath + "/WizardHintFields"): return
        if isNone(collectionObj.searchHintFields, collectionPath + "/SearchHintFields"): return
        if isNone(collectionObj.dropdownFields, collectionPath + "/DropdownFields"): return
        if isNone(collectionObj.enumValues, enumValuePath): return

        assert collectionObj.searchField in ["id", "code", "text"]

        assert collectionObj.enumValues is not None
        for enumValueObj in collectionObj.enumValues:
            if isNone(enumValueObj.id, "Id"): return
            if isNone(enumValueObj.code, "Code"): return
            if isNone(enumValueObj.text, "Text"): return
            if isNone(enumValueObj.isUnknown, "IsUnknown"): return
            if isNone(enumValueObj.isNotRelevant, "IsNotRelevant"): return

    assert config.defaultConfiguration is not None
    if config.defaultConfiguration.defaultCollection not in config.collections:
        config = None
        error_description = "Collection name in root/DefaultConfiguration/DefaultCollection not found in root/Collections"
        return
