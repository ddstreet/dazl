
from functools import cached_property

from ..exception import ConfigError
from . import DazlObject
from . import FBVFallbackObject
from . import NamedDazlObject
from .build import Build
from .dist_git import DistGit
from .overlay import Overlay


class Component(DazlObject):
    _KEY_CLASSMAP = {
        'spec': DistGit,
        'overlays': Overlay,
        'build': Build,
    }
    _KEY_DEFAULTS = {
        'release': {'calculation': 'auto'},
    }


class NamedComponent(Component, NamedDazlObject):
    pass


class NamedComponent(FBVFallbackObject, Component, NamedDazlObject):
    @cached_property
    def _fallback_list(self):
        groups = self._top_object.component_groups
        my_groups = []
        for name in groups:
            group = getattr(groups, name)
            if self._name in group.components:
                my_groups.append(group.default_component_config)

        return my_groups
