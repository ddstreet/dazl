
from . import TomlObject
from .dist_git import DistGit


class Component(TomlObject):
    _KEY_CLASSMAP = {
        'spec': DistGit,
        'dist_git': DistGit,
    }

    def get_name(self):
        return self._parent_attr

    def get_dist_git(self):
        try:
            return self.dist_git
        except AttributeError:
            return self.spec


class Components(TomlObject):
    def _get_value_class(self, key, value):
        return Component
