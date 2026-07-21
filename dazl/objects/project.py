
from functools import cache

from ..exception import ConfigError
from ..exception import NoConfig
from . import Conversions
from . import DazlObject


class DefaultDistro(DazlObject):
    _KEY_DEFAULTS = {
        'name': '',
        'version': '',
        'snapshot': '',
    }


class Project(DazlObject):
    _KEY_CLASSMAP = {
        'default_distro': DefaultDistro,
    }
    _KEY_CONVERSIONS = {
        'dist_git_dir': Conversions.resolve_path,
        'rendered_specs_dir': Conversions.resolve_path,
    }

    @property
    def dist_git_dir(self):
        try:
            return super().dist_git_dir
        except AttributeError:
            return self.rendered_specs_dir

    @cache
    def get_default_distro(self):
        try:
            return getattr(self._top_object.distros, self.default_distro.name)
        except AttributeError:
            raise ConfigError(f"No configuration found for distro name '{self.default_distro.name}'")

    @cache
    def get_default_distro_version(self):
        # remove once default version is moved into project
        version = self.default_distro.version or self.get_default_distro().default_version

        try:
            return getattr(self.get_default_distro().versions, version)
        except AttributeError:
            raise ConfigError(f"No configuration found for distro name '{self.default_distro.name}' version '{self.default_distro.version}'")
