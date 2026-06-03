
from . import DazlObject


class Build(DazlObject):
    _KEY_DEFAULTS = {
        'with': [],
        'without': [],
        'defines': {},
        'undefines': [],
        'check': {'skip': False},
    }
