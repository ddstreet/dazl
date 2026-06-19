
from . import TomlObject


class DistroVersion(TomlObject):
    _KEY_DEFAULTS = {
        'description': '',
        'dist_git_branch': '',
        'default_component_config': {},
        'mock_config_x86_64': '',
        'mock_config_aarch64': '',
    }
