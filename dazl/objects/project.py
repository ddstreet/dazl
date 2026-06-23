
from ..exception import ConfigurationError
from ..exception import NoConfiguration
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
            raise NoConfiguration('Project has no default distro')

        try:
            distro = getattr(self._top_object.distros, name)
        except AttributeError:
            raise ConfigurationError(f"No configuration found for distro name '{name}'")

        version = self.default_distro.version
        if not version:
            version = distro.default_version

        try:
            return = getattr(distro, version)
        except AttributeError:
            raise ConfigurationError(f"No configuration found for distro name '{name}' version '{version}'")
