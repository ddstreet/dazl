

class NoConfig(Exception):
    pass


class ConfigError(Exception):
    pass


class GitError(Exception):
    pass


class NotGitRepo(GitError):
    pass


class NotDistGitRepo(GitError):
    pass


class SpecError(Exception):
    pass


class AutoreleaseError(SpecError):
    pass


class NotAutoreleaseSpec(AutoreleaseError):
    pass
