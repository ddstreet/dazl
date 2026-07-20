
from . import DazlObject


class Overlay(DazlObject):
    def __eq__(self, other):
        if not isinstance(other, Overlay):
            return False

        return self._json == other._json
