
from . import TomlObject
from . import TomlMap
from .component import Components
from .distro import Distros
from .project import Project


class TopObject(TomlObject):
    _KEY_CLASSMAP = {
        'components': Components,
        'distros': Distros,
        'project': Project,
    }

    def __init__(self, top_toml_file):
        super().__init__(TomlMap(top_toml_file))
