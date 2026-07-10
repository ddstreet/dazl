
import subprocess

from contextlib import contextmanager
from functools import cache
from functools import cached_property
from pathlib import Path
from tempfile import TemporaryDirectory

from .exception import GitError


class Git:
    @classmethod
    def git_cmd_stdout(cls, cmd, cwd=None):
        try:
            return (subprocess.run(['git'] + cmd, cwd=cwd, check=True, text=True, capture_output=True).stdout or '').strip()
        except subprocess.CalledProcessError as cpe:
            raise GitError(f"Git command 'git {' '.join(cmd)}' failed: {cpe}")

    @classmethod
    @contextmanager
    def _clone_from_repo(cls, src, *, is_remote, commit=None):
        with TemporaryDirectory() as tempdir:
            destdir = Path(tempdir) / 'dazl_git_clone'
            cmd = ['clone', '--revision', commit or 'HEAD']
            if not is_remote:
                cmd += ['-s']
            cmd += [str(src), str(destdir)]
            cls.git_cmd_stdout(cmd)
            yield destdir

    @classmethod
    @contextmanager
    def clone_from_remote(cls, remote, *, commit=None):
        with cls._clone_from_repo(remote, is_remote=True, commit=commit) as clone:
            yield clone

    @classmethod
    @contextmanager
    def clone_from_local(cls, local, *, commit=None):
        with cls._clone_from_repo(local, is_remote=False, commit=commit) as clone:
            yield clone

    def __init__(self, source=Path.cwd()):
        self.source = Path(source)
        self.sourcedir = self.source.parent if self.source.is_file() else self.source
        if not self.sourcedir.exists():
            raise FileNotFoundError(self.sourcedir)

    @cached_property
    def topleveldir(self):
        return Path(self.git_cmd_stdout(['rev-parse', '--show-toplevel'], cwd=self.sourcedir))

    def relative_path(self, path=None):
        path = self.source if path is None else Path(path)
        return path.relative_to(self.topleveldir)

    @cache
    def get_hash(self, commit):
        return self.git_cmd_stdout(['rev-parse', '--verify', '--end-of-options', commit], cwd=self.sourcedir)

    @contextmanager
    def clone_at_commit(self, commit):
        with self.clone_from_local(self.sourcedir, commit=self.get_hash(commit)) as clone:
            yield clone / self.relative_path()
