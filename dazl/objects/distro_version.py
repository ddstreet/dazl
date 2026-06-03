
from . import DazlObject
from . import NamedDazlObject
from .component import Component


class DistroVersion(DazlObject):
    _KEY_CLASSMAP = {
        'default_component_config': Component,
    }
    _KEY_DEFAULTS = {
        'dist_git_branch': '',
        'mock_config_x86_64': '',
        'mock_config_aarch64': '',
    }


class NamedDistroVersion(DistroVersion, NamedDazlObject):
    pass
