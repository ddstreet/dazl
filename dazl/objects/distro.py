
from . import DazlObject
from .distro_version import DistroVersion


class Distro(DazlObject):
    _KEY_CLASSMAP = {
        # 'versions': DistroVersion._collection_class(),
    }
    _KEY_DEFAULTS = {
        'description': '',
        'dist_git_base_uri': '',
        'lookaside_base_uri': '',
        'repos': []
    }
