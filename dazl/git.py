
import subprocess

from contextlib import contextmanager
from contextlib import suppress
from functools import cache
from functools import cached_property
from pathlib import Path
from specfile.specfile import Specfile
from tempfile import TemporaryDirectory

from .exception import GitError
from .exception import NotAutoreleaseSpec
from .exception import NotDistGitRepo
from .exception import NotGitRepo


DAZL_CONFIG_CLONED_FROM = 'dazl.clonedfrom'


class Git:
    @classmethod
    def _cmd_stdout(cls, cmd, cwd=None, errmsg="Cmd '{cmd}' failed: {err}"):
        cmd = list(map(str, cmd))
        print(f"Running: {' '.join(cmd)}")
        try:
            return (subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True).stdout or '').strip()
        except subprocess.CalledProcessError as cpe:
            raise GitError(errmsg.format(cmd=' '.join(cmd), err=cpe.stderr))

    @classmethod
    def cmd_git_stdout(cls, cmd, cwd=None):
        return cls._cmd_stdout(['git'] + cmd, cwd=cwd)

    @classmethod
    def get_topleveldir_for_path(self, path):
        path = Path(path)
        if path.is_file():
            path = path.parent
        try:
            return Path(self.cmd_git_stdout(['rev-parse', '--show-toplevel'], cwd=path))
        except GitError as ge:
            raise NotGitRepo(f"Git repo not found at '{path}': {ge}")

    @classmethod
    @contextmanager
    def get_clonedir_from_repo(cls, src, *, commit=None, readonly=True):
        cmd = ['clone']
        commit = commit or 'HEAD'

        cloning_from_remote = not Path(src).is_dir()
        if not cloning_from_remote:
            # The git -s arg creates a repo that 'shares' its objects
            # with the repo it's cloned from, meaning changes to it
            # can affect the src repo; so don't modify the clone repo
            # unless 'readonly' is set to False
            cmd += ['-s' if readonly else '--no-local']
            # Clone *only* the specific commit (and its history) that
            # we care about
            cmd += ['--revision', commit]
            # Tell future calls to this method to clone from the
            # original repo, not the (possibly partial) clone we
            # previously created
            cmd += ['--config', f'{DAZL_CONFIG_CLONED_FROM}=origin']
            # Check the src repo for the config setting telling us to
            # clone from the original repo (as mentioned above)
            with suppress(GitError):
                cloned_from = cls.cmd_git_stdout(['config', 'get', '--local', DAZL_CONFIG_CLONED_FROM], cwd=src)
                src = cls.cmd_git_stdout(['remote', 'get-url', cloned_from], cwd=src)

        with TemporaryDirectory() as tempdir:
            clonedir = Path(tempdir) / f'dazl_git_clone_at_{commit}'
            cmd += [str(src), str(clonedir)]
            cls.cmd_git_stdout(cmd)

            if cloning_from_remote:
                # Unfortunately, we can't clone only a specific commit
                # from a remote, only from the commits is 'advertises'
                # (i.e. git ls-remote). So we clone the whole remote
                # repo and checkout the commit we want.
                cls.cmd_git_stdout(['checkout', commit], cwd=clonedir)

            yield clonedir
        
    @classmethod
    @contextmanager
    def get_clone_from_repo(cls, src, **kwargs):
        with cls.get_clonedir_from_repo(src, **kwargs) as clonedir:
            yield cls(clonedir)

    def __init__(self, path=None):
        self.__topleveldir = self.get_topleveldir_for_path(path or Path.cwd())

    @property
    def topleveldir(self):
        return self.__topleveldir

    def relative_path(self, path, at=None):
        path = Path(path)
        if not path.is_absolute():
            path = (at or self.topleveldir).resolve() / path
        return path.resolve().relative_to(self.topleveldir)

    @cached_property
    def commit_hash(self):
        return self.get_hash_for_commit()

    @cache
    def get_hash_for_commit(self, commit=None):
        return self.cmd_git_stdout(['rev-parse', '--verify', '--end-of-options', commit or 'HEAD'], cwd=self.topleveldir)

    @cache
    def get_commit_for_path(self, path):
        return self.cmd_git_stdout(['log', '-1', '--format=%H', self.relative_path(path)], cwd=self.topleveldir)

    @cache
    def get_commit_for_date(self, date):
        return self.cmd_git_stdout(['log', '-1', '--format=%H', '--before', date], cwd=self.topleveldir)

    def get_commit_range_log(self, start, end):
        return self.cmd_git_stdout(['log', '--oneline', start, end])

    @contextmanager
    def get_clonedir_at_commit(self, commit=None, **kwargs):
        with self.get_clonedir_from_repo(self.topleveldir, commit=self.get_hash_for_commit(commit), **kwargs) as clonedir:
            yield clonedir

    @contextmanager
    def get_clone_for_dist_git_dir(self, dist_git_dir, commit=None):
        with self.get_clonedir_at_commit(commit, readonly=False) as clonedir:
            self.cmd_git_stdout(['filter-repo', '--subdirectory-filter', self.relative_path(dist_git_dir)], cwd=clonedir)
            yield DistGit(clonedir)


class DistGit(Git):
    @classmethod
    def cmd_rpmautospec_stdout(cls, cmd, cwd=None):
        return cls._cmd_stdout(['rpmautospec'] + cmd, cwd=cwd, errmsg="Autorelease command '{cmd}' failed: {err}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        matches = list(self.topleveldir.glob('*.spec'))
        if not matches:
            raise NotDistGitRepo(f"Invalid dist-git repo '{self.topleveldir}' has no spec file")
        if len(matches) > 1:
            raise NotDistGitRepo(f"Invalid dist-git repo '{self.topleveldir}' has too many ({len(matches)}) spec files")
        self.__spec = matches[0]

    @property
    def spec(self):
        return self.__spec

    @cached_property
    def specfile(self):
        return Specfile(path=self.spec)

    @cache
    def get_spec_changelog(self):
        return str(self.specfile.changelog().content)

    @cache
    def get_autorelease_changelog(self):
        if not self.specfile.has_autochangelog:
            raise NotAutoreleaseSpec(f"Spec file '{self.spec}' does not use %autochangelog")
        return self.cmd_rpmautospec_stdout(['generate-changelog', self.spec])

    @cache
    def get_changelog(self):
        with suppress(NotAutoreleaseSpec):
            return self.get_autorelease_changelog()
        return self.get_spec_changelog()
