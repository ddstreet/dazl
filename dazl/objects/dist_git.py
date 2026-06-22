
from functools import cached_property

from . import DazlObject


class DistGit(DazlObject):
    @classmethod
    def _get_instance_class(cls, key, value, *, parent, parent_attr=None):
        if value.get('type') == 'local':
            return LocalDistGit
        if value.get('type') == 'upstream':
            return UpstreamDistGit
        return super()._get_instance_class(key, value, parent=parent, parent_attr=parent_attr)


class LocalDistGit(DistGit):
    def _check_instance(self):
        assert self.type == 'local'

    @cached_property
    def path(self):
        return self._resolve_relative_path(super().path)


class UpstreamDistGit(DistGit):
    def _check_instance(self):
        assert self.type == 'upstream'
