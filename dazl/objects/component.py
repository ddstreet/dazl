
from . import DazlObject
from .dist_git import DistGit
from .overlay import Overlay
from .build import Build


class Component(DazlObject):
    _KEY_CLASSMAP = {
        'spec': DistGit,
        'overlays': Overlay,
        'build': Build,
    }
    _KEY_DEFAULTS = {
        'release': {'calculation': 'auto'},
    }
