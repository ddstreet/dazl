
from functools import cached_property

from . import TomlObject


class Project(TomlObject):
    @cached_property
    def rendered_specs_dir(self):
        return self._resolve_relative_path(super().rendered_specs_dir)
