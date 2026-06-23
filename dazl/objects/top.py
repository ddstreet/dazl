
from . import TopDazlObject
from .component import NamedComponent
from .component_group import NamedComponentGroup
from .distro import NamedDistro
from .project import Project


class TopObject(TopDazlObject):
    _KEY_CLASSMAP = {
        'component_groups': NamedComponentGroup._get_named_object_list_class(),
        'components': NamedComponent._get_named_object_list_class(),
        'distros': NamedDistro._get_named_object_list_class(),
        'project': Project,
    }
