
from functools import cached_property

from . import TomlObject
from .dist_git import DistGit
from .overlay import Overlay
from .build import Build


class Component(TomlObject):
    _KEY_CLASSMAP = {
        'spec': DistGit,
        'dist_git': DistGit,
        'overlays': Overlay,
        'build': Build,
    }
    _KEY_DEFAULTS = {
        'overlays': [],
    }

    @cached_property
    def release(self):
        try:
            return super().release
        except AttributeError:
            return {'calculation': 'auto'}

    @cached_property
    def build(self):
        try:
            return super().build
        except AttributeError:
            return Build._create_empty_instance({}, self)

    @property
    def spec(self):
        return self.dist_git

    @cached_property
    def dist_git(self):
        try:
            return super().dist_git
        except AttributeError:
            try:
                return super().spec
            except AttributeError:
                return DistGit._create_empty_instance({}, self)
