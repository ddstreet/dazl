
from . import TomlObject


class Build(TomlObject):
    _KEY_DEFAULTS = {
        'with': [],
        'without': [],
        'defines': {},
        'undefines': [],
        'check': {'skip': False},
    }
