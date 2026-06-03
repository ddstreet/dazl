
from functools import cache

from . import TomlObject


class DistGit(TomlObject):
    @classmethod
    def _get_instance_class(cls, key, value, *, parent, parent_attr=None):
        if value.get('type') == 'local':
            return LocalDistGit
        if value.get('type') == 'upstream':
            return UpstreamDistGit
        return super()._get_instance_class(key, value, parent=parent, parent_attr=parent_attr)

    def get_name(self):
        return self._parent_attr


class LocalDistGit(DistGit):
    def _check_instance(self):
        if self.type != 'local':
            raise TypeError(f"LocalDistGit type must be 'local', got '{self.type}'")

    @cache
    def get_local_spec_file(self):
        return self._resolve_relative_path(self.path)


class UpstreamDistGit(DistGit):
    def _check_instance(self):
        if self.type != 'upstream':
            raise TypeError(f"UpstreamDistGit type must be 'upstream', got '{self.type}'")
