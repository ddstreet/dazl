
from . import Conversions
from . import DazlObject
from . import NamedDazlObject
from .distro_version import NamedDistroVersion


class Distro(DazlObject):
    _KEY_CLASSMAP = {
        'versions': NamedDistroVersion._get_named_object_collection_class(),
    }
    _KEY_DEFAULTS = {
        'dist_git_base_uri': '',
        'lookaside_base_uri': '',
        'repos': []
    }
    _KEY_CONVERSIONS = {
        'default_version': Conversions.dashes_to_underscores,
    }


class NamedDistro(Distro, NamedDazlObject):
    pass
