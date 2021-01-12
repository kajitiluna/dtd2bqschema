from pathlib import Path
from typing import List, Dict, Set, Optional, Union

from lark import Lark, Tree

from .dtddefinition import (
    BqColumnType,
    BqColumnMode,
    BqSchema,
    BqUnitSchema,
    BqRecordSchema,
    ConstantDef,
    ElementDef,
    ElementTermDef,
    ElementFactorDef,
    RefElementDef,
    RefEntityDef,
    ElementAttributeDef,
    EntityDef,
    EntityAvailableDef
)
from .dtdtransformer import DtdTransformer


class InvalidDefinition(Exception):
    def __init__(self, column_type: Optional[BqColumnType], column_mode: BqColumnMode = BqColumnMode.NULLABLE):
        self.column_type: Optional[BqColumnType] = column_type
        self.column_mode: BqColumnMode = column_mode


class DtdSchema():
    def __init__(self, converted: list,
                 element_column: str = "detail"):

        elements: Dict[str, ElementDef] = {}
        element_attributes: Dict[str, ElementAttributeDef] = {}
        entities: Dict[str, EntityDef] = {}
        entity_availalbles: Dict[str, EntityAvailableDef] = {}
        for target in converted:
            target_class = type(target)
            if target_class == ElementDef:
                elements[target.element_name] = target
            elif target_class == ElementAttributeDef:
                element_attributes[target.element_name] = target
            elif target_class == EntityDef:
                entities[target.entity_name] = target
            elif target_class == EntityAvailableDef:
                entity_availalbles[target.entity_name] = target

        self.elements: Dict[str, ElementDef] = elements
        self.element_attributes: Dict[str,
                                      ElementAttributeDef] = element_attributes
        self.entities: Dict[str, EntityDef] = entities
        self.entity_availalbles: Dict[str,
                                      EntityAvailableDef] = entity_availalbles

        self.sub_column: str = element_column
        self.not_founds_element: Set[str] = set()

    def to_json(self, element_name: str) -> BqSchema:
        element: ElementDef = self.elements[element_name]
        return self.to_json_element(element)

    def to_json_element(self, element: ElementDef) -> Optional[BqSchema]:

        attribute_info: Optional[ElementAttributeDef] = \
            self.element_attributes.get(element.element_name)

        if isinstance(element.sub_element, ConstantDef) is True:
            column_type: Optional[BqColumnType] = element.sub_element.value_type(
            )
            return self._to_json_constant(
                element.element_name, column_type, BqColumnMode.REQUIRED, attribute_info
            )

        try:
            sub_schemas: List[BqSchema] = self.to_json_base(
                element.sub_element)
        except InvalidDefinition as invalid:
            return self._to_json_constant(
                element.element_name, invalid.column_type, invalid.column_mode, attribute_info
            )

        if len(sub_schemas) == 0:
            return None

        if attribute_info is None:
            return BqRecordSchema(element.element_name, fields=sub_schemas)

        fields: List[BqSchema] = attribute_info.to_json() + sub_schemas
        return BqRecordSchema(element.element_name, fields=fields, column_mode=BqColumnMode.REQUIRED)

    def _to_json_constant(self, element_name: str, column_type: Optional[BqColumnType], column_mode: BqColumnMode,
                          attribute_info: Optional[ElementAttributeDef]):

        if column_type is None:
            # Not support "<!ELEMENT ... ANY>"
            if attribute_info is None:
                return BqUnitSchema(element_name, column_type=BqColumnType.STRING, column_mode=column_mode)
            return BqRecordSchema(
                element_name, fields=attribute_info.to_json(),
                column_mode=attribute_info.summary_type()
            )

        if attribute_info is None:
            return BqUnitSchema(element_name, column_type=column_type, column_mode=column_mode)

        fields: List[BqSchema] = attribute_info.to_json() + [
            BqUnitSchema(self.sub_column, column_type=column_type,
                         column_mode=column_mode)
        ]
        return BqRecordSchema(element_name, fields=fields, column_mode=BqColumnMode.REQUIRED)

    def to_json_base(self, base) -> List[BqSchema]:
        if isinstance(base, ConstantDef) is True:
            raise InvalidDefinition(base.value_type())

        if isinstance(base, RefElementDef) is True:
            sub_schema: Optional[BqSchema] = self._to_json_inner_element(
                base)
            return [sub_schema] if sub_schema is not None else []

        if isinstance(base, RefEntityDef) is True:
            exchangaed: Optional[ElementTermDef] = self._exchange_entity(base)
            return self.to_json_term(exchangaed) if exchangaed is not None else []

        return self.to_json_term(base)

    def _to_json_inner_element(self, ref: RefElementDef) -> Optional[BqSchema]:
        sub_element: Optional[ElementDef] = self.elements.get(ref.element_name)
        if sub_element is None:
            self.not_founds_element.add(ref.element_name)
            return None

        return self.to_json_element(sub_element)

    def _exchange_entity(self, ref: RefEntityDef) -> Optional[ElementTermDef]:
        sub_entity: Optional[EntityDef] = self.entities.get(ref.entity_name)
        if sub_entity is None:
            return None
        if isinstance(sub_entity.contents, (tuple, EntityDef)) is True:
            return None

        return sub_entity.contents

    def to_json_term(self, term) -> List[BqSchema]:
        if isinstance(term, ElementTermDef) is False:
            schema: List[BqSchema] = self.to_json_factor(term)
            return schema

        schemas: List[BqSchema] = []
        for factor in term.nodes:
            schema: List[BqSchema] = self.to_json_factor(factor)
            schemas.extend(schema)

        return schemas

    def to_json_factor(self, factor) -> List[BqSchema]:
        if isinstance(factor, ElementFactorDef) is False:
            return self.to_json_base(factor)

        try:
            factor_schemas: List[BqSchema] = self.to_json_base(factor.node)
            return [factor.mode(factor_schema) for factor_schema in factor_schemas] \
                if len(factor_schemas) > 0 else []
        except InvalidDefinition as invalid:
            raise InvalidDefinition(invalid.column_type, factor.column_mode())


class Dtd2BqSchema():

    def __init__(self):
        lark_file: Path = Path(__file__).parent / "dtd.lark"
        self.parser: Lark = Lark.open(
            lark_file, start="dtd", propagate_positions=True)

    def parse_from_file(self, file_path: Union[Path, str], top_node: str) -> BqSchema:
        with open(file_path) as file:
            dtd_str: str = file.read()

        return self.parse_from_string(dtd_str, top_node)

    def parse_from_string(self, dtd_str: str, top_node: str) -> BqSchema:
        result: Tree = self.parser.parse(dtd_str)
        converted: list = DtdTransformer().transform(result)

        schema: DtdSchema = DtdSchema(converted)
        return schema.to_json(top_node)
