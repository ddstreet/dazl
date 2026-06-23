
from . import DazlObject
from .distro_version import DistroVersion


class Distro(DazlObject):
    _KEY_CLASSMAP = {
        'versions': DistroVersion._get_named_object_list_class(),
    }
    _KEY_DEFAULTS = {
        'dist_git_base_uri': '',
        'lookaside_base_uri': '',
        'repos': []
    }
