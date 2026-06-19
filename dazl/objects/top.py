
from . import TomlObject
from . import TomlMap
from .component import Component
from .component_group import ComponentGroup
from .distro import Distro
from .project import Project


class TopObject(TomlObject):
    _KEY_CLASSMAP = {
        'component_groups': ComponentGroup._collection_class(),
        'components': Component._collection_class(),
        'distros': Distro._collection_class(),
        'project': Project,
    }

    def __init__(self, top_toml_file):
        super().__init__(TomlMap(top_toml_file))
