
from . import TomlObject
from .component import Component


class ComponentGroup(TomlObject):
    _KEY_CLASSMAP = {
        'default_component_config': Component,
    }
    _KEY_DEFAULTS = {
        'description': '',
        'components': [],
        'default_component_config': {},
    }
