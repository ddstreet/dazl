
from . import DazlObject
from . import NamedDazlObject


class DistroVersion(DazlObject):
    _KEY_DEFAULTS = {
        'dist_git_branch': '',
        'default_component_config': {},
        'mock_config_x86_64': '',
        'mock_config_aarch64': '',
    }


class NamedDistroVersion(DistroVersion, NamedDazlObject):
    pass
