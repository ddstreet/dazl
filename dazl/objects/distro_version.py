
from . import DazlObject


class DistroVersion(DazlObject):
    _KEY_DEFAULTS = {
        'dist_git_branch': '',
        'default_component_config': {},
        'mock_config_x86_64': '',
        'mock_config_aarch64': '',
    }
