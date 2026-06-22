
from functools import cached_property

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

    @cached_property
    def release(self):
        try:
            return super().release
        except AttributeError:
            return {'calculation': 'auto'}
