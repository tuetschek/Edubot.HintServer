from typing import TypeVar, Optional

import hint_server.models as models

T = TypeVar("T")

def asNotNone(value: Optional[T]) -> T:
    assert value is not None
    return value

def downgradeSearchHint2EnumItem(searchHint: models.SearchHint, collectionConfig: models.CollectionConfiguration) -> list[models.EnumItem]:
    downgraded = []
    for field, fieldValue in asNotNone(searchHint.fieldsAndValues).items():
        print(field, fieldValue)
        configEnumValue = list(filter(lambda x: x.text == fieldValue, asNotNone(collectionConfig.enumValues)))
        if len(configEnumValue) == 0: continue
        item = models.EnumItem()
        item.id = configEnumValue[0].id
        item.valueCode = configEnumValue[0].code
        item.enumType = field
        downgraded.append(item)
    return downgraded
    
def downgradeWizardHint2EnumList(wizardHint: models.WizardHint, collectionConfig: models.CollectionConfiguration) -> models.EnumList:
    downgraded = models.EnumList()
    downgraded.enumType = wizardHint.field
    downgraded.values = []
    for fieldValue in asNotNone(wizardHint.values):
        configFieldValues : list[models.CollectionConfigurationEnumValue] = list(filter(lambda x: x.text == fieldValue, asNotNone(collectionConfig.enumValues)))
        if len(configFieldValues) == 0: continue
        for configFieldValue in configFieldValues:
            item = models.EnumListItem()
            item.id = configFieldValue.id
            item.valueCode = configFieldValue.code
            downgraded.values.append(item) 
    return downgraded
