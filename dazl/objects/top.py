
from . import DazlTopObject
from .component import Component
from .component_group import ComponentGroup
from .distro import Distro
from .project import Project


class TopObject(DazlTopObject):
    _KEY_CLASSMAP = {
        'component_groups': ComponentGroup._get_named_object_list_class(),
        'components': Component._get_named_object_list_class(),
        'distros': Distro._get_named_object_list_class(),
        'project': Project,
    }

    def __init__(self, top_toml_file):
        super().__init__(top_toml_file)
