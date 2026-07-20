
from functools import cached_property
from pathlib import Path

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
        'overlays': Overlay._get_object_collection_class(),
        'build': Build,
    }
    _KEY_DEFAULTS = {
        'release': {'calculation': 'auto'},
    }
    _KEY_IGNORES = [
        'publish',
    ]

    def __eq__(self, other):
        if not isinstance(other, Component):
            return False

        return all((self.spec._json == other.spec._json,
                    self.build._json == other.build._json,
                    self.release.calculation == other.release.calculation,
                    self.overlays == other.overlays))


class NamedComponent(Component, NamedDazlObject):
    @property
    def dist_git_dir(self):
        return str(Path(self._top_object.project.dist_git_dir) / self._name[0].lower() / self._name)

    def get_last_release_commit(self):
        return self._top_object._toml_git.get_commit_for_path(self.dist_git_dir)

    def do_release(self, dest=None):
        if not dest:
            dest = self._top_object.project.dist_git_dir / self._name[0].lower() / self._name

        # get upstream dist-git

        # place upstream dist-git files into dest

        # run overlays (and other transforms)

        # autorelease


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
