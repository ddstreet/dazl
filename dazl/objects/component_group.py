
from . import DazlObject
from . import NamedDazlObject
from .component import Component


class ComponentGroup(DazlObject):
    _KEY_CLASSMAP = {
        'default_component_config': Component,
    }
    _KEY_DEFAULTS = {
        'components': [],
        'default_component_config': {},
    }


class NamedComponentGroup(ComponentGroup, NamedDazlObject):
    pass
