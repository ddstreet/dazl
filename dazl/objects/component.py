
from functools import cached_property

from ..exception import ConfigError
from ..exception import NoConfig
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
    _KEY_IGNORES = [
        'publish',
    ]


class NamedComponent(Component, NamedDazlObject):
    pass


class NamedComponentWithFallback(FBVFallbackObject, NamedComponent):
    @cached_property
    def _fallback_list(self):
        return self._fallback_component_groups + self._fallback_project_distro_group

    @property
    def _fallback_component_groups(self):
        return [group.default_component_config
                for group in self._top_object.component_groups._values()
                if self._name in group.components]

    @property
    def _fallback_project_distro_group(self):
        try:
            return [self._top_object.project.get_default_distro_version().default_component_config]
        except NoConfig:
            return []
