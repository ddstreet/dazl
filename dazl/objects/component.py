
import shutil

from contextlib import contextmanager
from functools import cached_property
from pathlib import Path

from ..exception import ConfigError
from ..exception import NoConfig
from ..exception import NotDistGitRepo
from . import DazlObject
from . import FBVFallbackObject
from . import NamedDazlObject
from .build import Build
from .dist_git import LocalDistGit
from .dist_git import UpstreamDistGit
from .overlay import Overlay


class Component(DazlObject):
    _KEY_CLASSMAP = {
        'overlays': Overlay._get_object_collection_class(),
        'build': Build,
    }
    _KEY_DEFAULTS = {
        'release': {'calculation': 'auto'},
    }
    _KEY_ALIASES = {
        'spec': 'dist_git',
        'dist_git': 'spec',
    }
    _KEY_IGNORES = [
        'publish',
    ]

    @classmethod
    def _get_object_class(cls, fbv, key):
        if key not in ['spec', 'dist_git']:
            return super()._get_object_class(fbv, key)

        spec_type = fbv.get('type').value
        if spec_type == 'local':
            return LocalDistGit
        elif spec_type == 'upstream':
            return UpstreamDistGit
        else:
            raise ConfigError(f"Invalid spec type '{spec_type}'")

    def __eq__(self, other):
        if not isinstance(other, Component):
            return False

        return all((self.spec._json == other.spec._json,
                    self.build._json == other.build._json,
                    self.release.calculation == other.release.calculation,
                    self.overlays == other.overlays))


class NamedComponent(Component, NamedDazlObject):
    def get_local_dist_git_path(self):
        return Path(self._top_object.project.dist_git_dir) / self._name[0].lower() / self._name

    @contextmanager
    def get_local_dist_git_clone(self):
        with self._git.get_clone_for_dist_git_dir(self.get_local_dist_git_path()) as clone:
            yield clone

    @contextmanager
    def get_upstream_dist_git_clone(self):
        with self.dist_git.get_src(self._name) as repo:
            yield repo

    def get_last_release_commit(self):
        return self._git.get_commit_for_path(self.get_local_dist_git_path())

    @contextmanager
    def get_last_release_component(self):
        with self._top_object._get_top_object_at_commit(self.get_last_release_commit()) as top_object:
            yield getattr(top_object.components, self._name)

    def do_release(self):
        with self.get_upstream_dist_git_clone() as new_dist_git:
            # run overlays/transforms

            self._update_release_and_changelog(new_dist_git)

            dest = self.get_local_dist_git_path()
            if dest.is_dir():
                assert dest.is_relative_to(self._top_dir)
                shutil.rmtree(dest)
            shutil.copytree(new_dist_git.topleveldir, dest, ignore=shutil.ignore_patterns('.git'))

    def _update_release_and_changelog(self, new_dist_git):
        if self.release.calculation == 'manual':
            # 'manual' components handle release and changelog from the TOML
            return

        try:
            with self.get_local_dist_git_clone() as current_dist_git:
                if new_dist_git.specfile.has_autorelease:
                    self._update_autorelease(new_dist_git, current_dist_git)
                else:
                    self._update_bumpspec(new_dist_git, current_dist_git)
        except NotDistGitRepo:
            # First-time creation of dist-git dir for this component
            with suppress(NotAutoreleaseSpec):
                # autorelease needs to have upstream's changelog put
                # in the changelog file, since we lose the upstream
                # dist-git commits
                new_dist_git.changelog.write_text(new_dist_git.get_autorelease_changelog())

    def _update_autorelease(self, new_dist_git, current_dist_git):
        new_specfile = new_dist_git.specfile
        if not new_specfile.has_autochangelog:
            raise SpecError(f'component {self._name}-{new_specfile.version}-{new_specfile.release} uses autorelease but not autochangelog?')

        print('updating autorelease pkg')
        with self.get_last_release_component() as last_release_component:
            if last_release_component.dist_git.is_remote and self.dist_git.is_remote:
                last_upstream_commit = last_release_component.dist_git.get_upstream_commit(self._name)
                new_upstream_commit = self.dist_git.get_upstream_commit(self._name)
                if last_upstream_commit != new_upstream_commit:
                    upstream_changes = new_dist_git.get_commit_range_log(last_upstream_commit, new_upstream_commit)
                    print(f'got upstream changes: {upstream_changes}')

        current_specfile = current_dist_git.specfile
        if current_specfile.has_autorelease:
            current_changelog_file = current_dist_git.topleveldir / 'changelog'
            if current_changelog_file.is_file():
                changelog_file_content = current_changelog_file.read_text()
            else:
                changelog_file_content = ''
        else:
            changelog_file_content = current_specfile.changelog().content
        new_changelog_file = new_dist_git.topleveldir / 'changelog'
        if changelog_file_content:
            new_changelog_file.write_text(changelog_file_content)
        else:
            new_changelog_file.unlink(missing_ok=True)

    def _update_bumpspec(self, src, current):
        # manual -> trad *- replace in-spec cl with prev cl, bumpspec
        # (l->u, u->uH, u->uNH)

        # auto -> trad *- replace in-spec cl with prev cl, bumpspec 
        # (l->u, u->uH)

        # trad -> trad *- replace in-spec cl with prev cl, bumpspec
        # (u->uH, u->uNH)

        pass


class NamedComponentWithFallback(FBVFallbackObject, NamedComponent):
    @cached_property
    def _fallback_list(self):
        return self._fallback_component_groups + self._fallback_project_distro_group

    @property
    def _fallback_component_groups(self):
        return [group.default_component_config
                for group in self._top_object.component_groups._values()
                if self._name in group.components]

    @property
    def _fallback_project_distro_group(self):
        try:
            return [self._top_object.project.get_default_distro_version().default_component_config]
        except NoConfig:
            return []
