
from . import TomlObject


class Distro(TomlObject):
    pass


class Distros(TomlObject):
    def _get_value_class(self, key, value):
        return Distro
