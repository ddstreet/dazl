
from ..exception import ConfigError
from ..exception import NoConfig
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

    def get_default_distro(self):
        name = self.default_distro.name
        if not name:
            raise NoConfig('Project has no default distro')

        try:
            distro = getattr(self._top_object.distros, name)
        except AttributeError:
            raise ConfigError(f"No configuration found for distro name '{name}'")

        version = self.default_distro.version
        if not version:
            version = distro.default_version

        try:
            return getattr(distro, version)
        except AttributeError:
            raise ConfigError(f"No configuration found for distro name '{name}' version '{version}'")
