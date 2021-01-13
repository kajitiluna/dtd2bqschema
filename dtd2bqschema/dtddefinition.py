from enum import Enum
from typing import List, Optional, Union
from abc import ABCMeta, abstractmethod
from collections import OrderedDict


class BqColumnType(Enum):
    STRING = "STRING"
    INTEGER = "INT64"
    FLOAT = "FLOAT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    RECORD = "RECORD"


class BqColumnMode(Enum):
    REQUIRED = "REQUIRED"
    NULLABLE = "NULLABLE"
    REPEATED = "REPEATED"


class BqSchema(metaclass=ABCMeta):
    def __init__(self, column_name: str,
                 column_type: BqColumnType,
                 column_mode: Optional[BqColumnMode] = BqColumnMode.NULLABLE):

        self.column_name: str = column_name
        self.column_type: BqColumnType = column_type
        self.column_mode: Optional[BqColumnMode] = column_mode

    def mode(self, column_mode: BqColumnMode):
        self.column_mode = column_mode
        return self

    def to_json(self):
        if self.column_mode is None:
            raise Exception("column_mode is not intialized.")

        return self.schema()

    @abstractmethod
    def schema(self) -> str:
        pass


class BqUnitSchema(BqSchema):
    def schema(self):
        return (
            "{"
            f'"name":"{self.column_name}"'
            f',"type":"{self.column_type.value}"'
            f',"mode":"{self.column_mode.value}"'
            "}"
        )


class BqRecordSchema(BqSchema):

    def __init__(self, column_name: str,
                 fields: List[BqSchema],
                 column_mode: Optional[BqColumnMode] = BqColumnMode.NULLABLE):

        super().__init__(column_name, BqColumnType.RECORD, column_mode)
        self.fields: List[BqSchema] = fields

    def schema(self):
        filtered_fields: List[BqSchema] = self._filter_same_columns()
        sub_jsons: List[str] = [sub_schema.to_json()
                                for sub_schema in filtered_fields]
        return (
            "{"
            f'"name":"{self.column_name}"'
            f',"type":"{self.column_type.value}"'
            f',"mode":"{self.column_mode.value}"'
            f',"fields":[{",".join(sub_jsons)}]'
            "}"
        )

    def _filter_same_columns(self) -> List[BqSchema]:
        filtered_fields: OrderedDict = OrderedDict()
        for sub_schema in self.fields:
            before: Optional[BqSchema] = filtered_fields.get(
                sub_schema.column_name)
            if before is not None:
                if (before.column_mode == BqColumnMode.REQUIRED) \
                        and (before.column_mode != sub_schema.column_mode):
                    filtered_fields[sub_schema.column_name] = sub_schema
                continue

            filtered_fields[sub_schema.column_name] = sub_schema

        return filtered_fields.values()


class ConstantDef(Enum):
    PCDATA = "#PCDATA"
    CDATA = "CDATA"
    NUMBER = "NUMBER"
    ID = "ID"
    NAME = "NAME"
    IDREF = "IDREF"
    IDREFS = "IDREFS"
    EMPTY = "EMPTY"
    ANY = "ANY"

    def value_type(self) -> Optional[BqColumnType]:
        if self.value in ("EMPTY", "ANY"):
            return None
        if self.value == "NUMBER":
            return BqColumnType.INTEGER
        return BqColumnType.STRING


class AttributePattern(Enum):
    IMPLIED = "#IMPLIED"
    REQUIRED = "#REQUIRED"
    FIXED = "#FIXED"
    VALUE = "(VALUE)"


class EntityAvailable(Enum):
    INCLUDE = "INCLUDE"
    IGNORE = "IGNORE"

    def __repr__(self):
        return self.value


class ElementDef():
    def __init__(self, element_name: str, sub_element):
        self.element_name: str = element_name
        self.sub_element: Union[
            ElementTermDef, ElementFactorDef, ConstantDef, RefElementDef, RefEntityDef
        ] = sub_element

    def __repr__(self):
        return f"ElementDef('{self.element_name}', {self.sub_element})"


class ElementTermDef():
    def __init__(self, children: list):
        self.nodes: List[Union[
            ElementFactorDef, ConstantDef, RefElementDef, RefEntityDef, ElementTermDef
        ]] = children

    def __repr__(self):
        return f"{type(self).__name__}({self.nodes})"


class SequenceFactorDef(ElementTermDef):
    pass


class AndFactorDef(ElementTermDef):
    pass


class OrFactorDef(ElementTermDef):
    pass


class ElementFactorDef(metaclass=ABCMeta):
    def __init__(self, child):
        self.node: Union[
            ConstantDef, RefElementDef, RefEntityDef, ElementTermDef, ElementFactorDef
        ] = child

    @abstractmethod
    def mode(self, schema: BqSchema) -> BqSchema:
        pass

    @abstractmethod
    def column_mode(self) -> BqColumnMode:
        pass

    def __repr__(self):
        return f"{type(self).__name__}({self.node})"


class MayRepeatElementDef(ElementFactorDef):
    def mode(self, schema: BqSchema) -> BqSchema:
        return schema.mode(BqColumnMode.REPEATED)

    def column_mode(self) -> BqColumnMode:
        return BqColumnMode.REPEATED


class MustRepeatElementDef(ElementFactorDef):
    def mode(self, schema: BqSchema) -> BqSchema:
        return schema.mode(BqColumnMode.REPEATED)

    def column_mode(self) -> BqColumnMode:
        return BqColumnMode.REPEATED


class OneOrNothingElementDef(ElementFactorDef):
    def mode(self, schema: BqSchema) -> BqSchema:
        return schema if schema.column_mode == BqColumnMode.REPEATED \
            else schema.mode(BqColumnMode.NULLABLE)

    def column_mode(self) -> BqColumnMode:
        return BqColumnMode.NULLABLE


class SubInElementDef(ElementFactorDef):
    def mode(self, schema: BqSchema) -> BqSchema:
        raise Exception("Not support for +element")

    def column_mode(self) -> BqColumnMode:
        raise Exception("Not support for +element")


class SubNotInElementDef(ElementFactorDef):
    def mode(self, schema: BqSchema) -> BqSchema:
        raise Exception("Not support for -element")

    def column_mode(self) -> BqColumnMode:
        raise Exception("Not support for -element")


class RefElementDef():
    def __init__(self, element_name: str):
        self.element_name: str = element_name

    def __repr__(self):
        return f"RefElementDef('{self.element_name}')"


class RefEntityDef():
    def __init__(self, entity_name: str):
        self.entity_name: str = entity_name

    def __repr__(self):
        return f"RefEntityDef('{self.entity_name}')"


class AttributeDef():
    def __init__(self, attribute_name: str,
                 attribute_type: Union[ConstantDef, RefElementDef],
                 default_pattern: AttributePattern):

        self.attribute_name: str = attribute_name
        self.attribute_type: Union[ConstantDef, RefElementDef] = attribute_type
        self.default_pattern: AttributePattern = default_pattern

    def to_json(self) -> BqSchema:
        attr_type: BqColumnType = self.attribute_type.value_type() \
            if type(self.attribute_type) == ConstantDef else BqColumnType.STRING

        return BqUnitSchema(self.attribute_name, column_type=attr_type,
                            column_mode=self.mode_type())

    def mode_type(self) -> BqColumnMode:
        return BqColumnMode.REQUIRED if (
            self.default_pattern == AttributePattern.REQUIRED) else BqColumnMode.NULLABLE

    def __repr__(self):
        return (
            f"AttributeDef('{self.attribute_name}'"
            f", {self.attribute_type} : {self.default_pattern})"
        )


class ElementAttributeDef():
    def __init__(self, element_name: str, attributes: List[AttributeDef]):
        self.element_name: str = element_name
        self.attributes: List[AttributeDef] = attributes

    def to_json(self) -> List[BqSchema]:
        return [attribute.to_json() for attribute in self.attributes]

    def summary_type(self) -> BqColumnMode:
        for attribute in self.attributes:
            if attribute.mode_type() == BqColumnMode.REQUIRED:
                return BqColumnMode.REQUIRED
        return BqColumnMode.NULLABLE

    def __repr__(self):
        return f"ElementAttributeDef('{self.element_name}', {self.attributes})"


class EntityDef():
    def __init__(self, entity_name: str, contents: list):
        self.entity_name: str = entity_name
        self.contents: Union[
            ElementTermDef, ElementFactorDef, tuple
        ] = contents

    def __repr__(self):
        return f"EntityDef('{self.entity_name}', {self.contents})"


class EntityAvailableDef():
    def __init__(self, entity_name: str, available: EntityAvailable):
        self.entity_name: str = entity_name
        self.available: EntityAvailable = available

    def __repr__(self):
        return f"EntityAvailableDef('{self.entity_name}', {self.available})"
