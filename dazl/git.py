
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
    def clone(self, commit):
        with TemporaryDirectory() as tempdir:
            commit_hash = self.get_hash(commit)
            clonedir = Path(tempdir) / commit_hash
            self.git_cmd_stdout(['clone', '-s', '--revision', commit_hash, str(self.sourcedir), str(clonedir)])
            yield clonedir / self.relative_path()
