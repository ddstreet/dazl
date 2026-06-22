
from . import DazlObject
from .component import Component


class ComponentGroup(DazlObject):
    _KEY_CLASSMAP = {
        'default_component_config': Component,
    }
    _KEY_DEFAULTS = {
        'description': '',
        'components': [],
        'default_component_config': {},
    }
