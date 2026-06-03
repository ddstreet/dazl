
from . import TopDazlObject
from .component import NamedComponentWithFallback
from .component_group import NamedComponentGroup
from .distro import NamedDistro
from .project import Project


class TopObject(TopDazlObject):
    _KEY_CLASSMAP = {
        'component_groups': NamedComponentGroup._get_named_object_collection_class(),
        'components': NamedComponentWithFallback._get_named_object_collection_class(),
        'distros': NamedDistro._get_named_object_collection_class(),
        'project': Project,
    }
