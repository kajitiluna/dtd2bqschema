
from lark import Transformer
from lark.tree import Tree

from .dtddefinition import (
    ConstantDef,
    AttributePattern,
    EntityAvailable,
    ElementDef,
    SequenceFactorDef,
    AndFactorDef,
    OrFactorDef,
    MayRepeatElementDef,
    MustRepeatElementDef,
    OneOrNothingElementDef,
    SubInElementDef,
    SubNotInElementDef,
    RefElementDef,
    RefEntityDef,
    ElementAttributeDef,
    AttributeDef,
    EntityDef,
    EntityAvailableDef
)


class DtdTransformer(Transformer):

    def dtd(self, children: list):
        return children

    def definition(self, children: list):
        return children[0]

    def element(self, children: list):
        return ElementDef(children[0].value, children[1])

    def ref_entity(self, children: list):
        return RefEntityDef(children[0])

    def ref_element(self, children: list):
        return RefElementDef(children[0])

    def sub_term(self, children: list):
        sub_node: Tree = children[0]
        if (isinstance(sub_node, Tree) is False) or (sub_node.data != 'sub_factor'):
            return sub_node

        return self.sub_factor(sub_node.children)

    def sub_sequence(self, children: list):
        return SequenceFactorDef(children)

    def sub_and(self, children: list):
        return AndFactorDef(children)

    def sub_or(self, children: list):
        return OrFactorDef(children)

    def sub_factor(self, children: list):
        sub_node: Tree = children[0]
        if (isinstance(sub_node, Tree) is False) or (sub_node.data != 'sub_element'):
            return sub_node

        return self.sub_element(sub_node.children)

    def sub_may_repeat(self, children: list):
        return MayRepeatElementDef(children[0])

    def sub_must_repeat(self, children: list):
        return MustRepeatElementDef(children[0])

    def sub_one_or_nothing(self, children: list):
        return OneOrNothingElementDef(children[0])

    def sub_in(self, children: list):
        return SubInElementDef(children[0])

    def sub_not_in(self, children: list):
        return SubNotInElementDef(children[0])

    def sub_element(self, children: list):
        sub_node: Tree = children[0]
        if (isinstance(sub_node, Tree) is False) or (sub_node.data != 'sub_term'):
            return sub_node

        return self.sub_term(sub_node.children)

    def attribute_list(self, children: list):
        return ElementAttributeDef(children[0].value, children[1:])

    def attribute(self, children: list):
        return AttributeDef(children[0].value, children[1], children[2])

    def attribute_types(self, children: list):
        return children[0]

    def attribute_type(self, children: list):
        return children[0]

    def attribute_values(self, children: list):
        return tuple(name.value for name in children)

    def attribute_pattern(self, children: list):
        return children[0]

    def implied(self, children: list):
        return AttributePattern.IMPLIED

    def required(self, children: list):
        return AttributePattern.REQUIRED

    def fixed(self, children: list):
        return AttributePattern.FIXED

    def value(self, children: list):
        return AttributePattern.VALUE

    def entity(self, children: list):
        if isinstance(children[1], EntityAvailable) is True:
            return EntityAvailableDef(children[0].value, children[1])
        return EntityDef(children[0].value, children[1])

    def entity_contents(self, children: list):
        return children[0]

    def entity_include(self, children: list):
        return EntityAvailable.INCLUDE

    def entity_ignore(self, children: list):
        return EntityAvailable.IGNORE

    def public_contents(self, children: list):
        return tuple(token.value for token in children)

    def any_contents(self, children: list):
        return " ".join([token.value for token in children])

    def entity_detail(self, children: list):
        return EntityDef(children[0].entity_name, children[1:])

    def pcdata(self, children: list):
        return ConstantDef.PCDATA

    def cdata(self, children: list):
        return ConstantDef.CDATA

    def number(self, children: list):
        return ConstantDef.NUMBER

    def id(self, children: list):
        return ConstantDef.ID

    def empty(self, children: list):
        return ConstantDef.EMPTY

    def any(self, children: list):
        return ConstantDef.ANY
