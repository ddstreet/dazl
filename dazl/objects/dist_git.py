
from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from contextlib import suppress
from functools import cached_property

from ..git import Git
from . import Conversions
from . import DazlObject


class DistGit(DazlObject, ABC):
    @abstractmethod
    @contextmanager
    def get_dist_git_src(self, component):
        pass


class LocalDistGit(DistGit):
    _KEY_CONVERSIONS = {
        'path': Conversions.resolve_path,
    }

    @contextmanager
    def get_dist_git_src(self, component):
        yield Path(self.path)


class UpstreamDistro(DazlObject):
    _KEY_DEFAULTS = {
        'snapshot': '',
    }


class UpstreamDistGit(DistGit):
    _KEY_CLASSMAP = {
        'upstream_distro': UpstreamDistro,
    }

    @contextmanager
    def get_dist_git_src(self, component):
        with Git.get_clonedir_from_repo(self.get_upstream_dist_git_url(component), commit=self.get_upstream_commit(component)) as clonedir:
            yield clonedir

    def get_upstream_distro(self):
        return getattr(self._top_object.distros, self.upstream_distro.name)

    def get_upstream_distro_version(self):
        return getattr(self.get_upstream_distro().versions, self.upstream_distro.version)

    def get_upstream_dist_git_url(self, component):
        return self.get_upstream_distro().dist_git_base_uri.replace('$pkg', component)

    def get_upstream_commit(self, component):
        with suppress(AttributeError):
            return self.upstream_commit

        with Git.get_clone_from_repo(self.get_upstream_dist_git_url(component), commit=self.get_upstream_distro_version().dist_git_branch) as clone:
            return clone.get_commit_for_date(self.upstream_distro.snapshot)
