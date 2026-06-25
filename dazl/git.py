
import subprocess

from contextlib import contextmanager
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

from .exception import GitError


class Git:
    @classmethod
    def git_cmd_stdout(cls, cmd, cwd=None):
        try:
            return (subprocess.run(['git'] + cmd, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout or '').strip()
        except subprocess.CalledProcessError as cpe:
            raise GitError(f"Git command 'git {' '.join(cmd)}' failed: {cpe}")

    @classmethod
    def toplevel(cls, source=None):
        return cls.git_cmd_stdout(['rev-parse', '--show-toplevel'], cwd=source)

    def __init__(self, source):
        source = Path(source)
        if source.is_file():
            source = source.parent
        if not source.exists():
            raise FileNotFoundError(source)
        self.source = Path(self.toplevel(source))

    @cache
    def commit_hash(self, commit):
        return self.git_cmd_stdout(['rev-parse', '--verify', '--end-of-options', commit], cwd=self.source)

    @contextmanager
    def clone_at_commit(self, commit):
        with TemporaryDirectory() as tempdir:
            commit_hash = self.commit_hash(commit)
            clonedir = tempdir / f'git_{commit_hash}'
            self.git_cmd_stdout(['clone', '-s', '--revision', commit_hash, str(self.source), str(clonedir)])
            yield clonedir
