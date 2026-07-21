
import subprocess

from contextlib import contextmanager
from contextlib import suppress
from functools import cache
from functools import cached_property
from pathlib import Path
from tempfile import TemporaryDirectory

from .exception import GitError
from .exception import NotGitRepo


CLONED_FROM_KEY = 'dazl.clonedfrom'


class Git:
    @classmethod
    def git_cmd_stdout(cls, cmd, cwd=None):
        try:
            return (subprocess.run(['git'] + cmd, cwd=cwd, check=True, text=True, capture_output=True).stdout or '').strip()
        except subprocess.CalledProcessError as cpe:
            raise GitError(f"Git command 'git {' '.join(cmd)}' failed: {cpe.stderr}")

    @classmethod
    def get_topleveldir_for_path(self, path):
        path = Path(path)
        if path.is_file():
            path = path.parent
        try:
            return Path(self.git_cmd_stdout(['rev-parse', '--show-toplevel'], cwd=path))
        except GitError as ge:
            raise NotGitRepo(f"Git repo not found at '{path}': {ge}")

    @classmethod
    def get_repo_cloned_from(cls, repo):
        with suppress(GitError):
            return cls.git_cmd_stdout(['config', 'get', '--local', CLONED_FROM_KEY], cwd=repo)
        return repo

    @classmethod
    def set_repo_cloned_from(cls, repo, cloned_from):
        cls.git_cmd_stdout(['config', 'set', '--local', CLONED_FROM_KEY, str(cloned_from)], cwd=repo)

    @classmethod
    @contextmanager
    def get_clonedir_from_repo(cls, src, *, from_local=False, commit=None):
        if from_local:
            src = cls.get_repo_cloned_from(src)
        commit = commit or 'HEAD'
        with TemporaryDirectory() as tempdir:
            clonedir = Path(tempdir) / f'dazl_git_clone_at_{commit}'
            cmd = ['clone', '--revision', commit]
            if from_local:
                cmd += ['-s']
            cmd += [str(src), str(clonedir)]
            cls.git_cmd_stdout(cmd)
            if from_local:
                cls.set_repo_cloned_from(clonedir, src)
            yield clonedir

    @classmethod
    @contextmanager
    def get_clone_from_repo(cls, src, *, from_local=False, commit=None):
        with cls.get_clonedir_from_repo(src, from_local=from_local, commit=commit) as clonedir:
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
        return self.get_hash_for_commit('HEAD')

    @cache
    def get_hash_for_commit(self, commit):
        return self.git_cmd_stdout(['rev-parse', '--verify', '--end-of-options', commit], cwd=self.topleveldir)

    @cache
    def get_commit_for_path(self, path):
        return self.git_cmd_stdout(['log', '-1', '--format=%H', str(self.relative_path(path))], cwd=self.topleveldir)

    @cache
    def get_commit_for_date(self, date):
        return self.git_cmd_stdout(['log', '-1', '--format=%H', '--before', str(date)], cwd=self.topleveldir)

    @contextmanager
    def get_clonedir_at_commit(self, commit):
        with self.get_clonedir_from_repo(self.topleveldir, from_local=True, commit=self.get_hash_for_commit(commit)) as clonedir:
            yield clonedir
