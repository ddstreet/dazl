
from functools import cached_property

from . import DazlObject
from . import FBVFallbackObject


class UpstreamDistro(DazlObject):
    pass


class UpstreamDistroWithFallback(FBVFallbackObject, UpstreamDistro):
    @cached_property
    def _fallback_list(self):
        return self._top_object.project.default_distro
