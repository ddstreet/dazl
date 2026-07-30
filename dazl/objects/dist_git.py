
from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from contextlib import suppress
from functools import cached_property

from ..git import DistGit as DistGitRepo
from ..git import Git
from . import Conversions
from . import DazlObject
from .upstream_distro import UpstreamDistroWithFallback


class DistGit(DazlObject, ABC):
    @abstractmethod
    @contextmanager
    def get_src(self, component):
        pass

    @property
    @abstractmethod
    def is_local(self):
        pass

    @property
    def is_remote(self):
        return not self.is_local


class LocalDistGit(DistGit):
    _KEY_CONVERSIONS = {
        'path': Conversions.resolve_path,
    }

    @contextmanager
    def get_src(self, component):
        with self._git.get_clone_for_dist_git_dir(self.path) as clone:
            yield clone

    @property
    def is_local(self):
        return True


class UpstreamDistGit(DistGit):
    _KEY_CLASSMAP = {
        'upstream_distro': UpstreamDistroWithFallback,
    }

    @contextmanager
    def get_src(self, component):
        with DistGitRepo.get_clone_from_repo(self.get_upstream_dist_git_url(component), commit=self.get_upstream_commit(component)) as clone:
            yield clone

    @property
    def is_local(self):
        return False

    def get_upstream_distro(self):
        return getattr(self._top_object.distros, self.upstream_distro.name)

    def get_upstream_distro_version(self):
        return getattr(self.get_upstream_distro().versions, self.upstream_distro.version)

    def get_upstream_dist_git_url(self, component):
        return self.get_upstream_distro().dist_git_base_uri.replace('$pkg', component)

    def get_upstream_commit(self, component):
        with suppress(AttributeError):
            return self.upstream_commit

        # Temp hack to cache upstream commit hashes until TOML object
        # model can be properly fixed
        if 'commit_cache' not in globals():
            global commit_cache
            commit_cache = {}

        upstream_url = self.get_upstream_dist_git_url(component)
        branch = self.get_upstream_distro_version().dist_git_branch
        commit_date = self.upstream_distro.snapshot
        cache_key = f'{upstream_url}:{branch}@{commit_date}'

        if cache_key not in commit_cache:
            with Git.get_clone_from_repo(upstream_url, commit=branch) as clone:
                commit_cache[cache_key] = clone.get_commit_for_date(commit_date)

        return commit_cache[cache_key]
