
import argcomplete
import argparse
import sys

from contextlib import contextmanager
from functools import cached_property

from . import DEFAULT_ROOT_TOML_FILE
from .component import Component
from .objects.top import TopObject


class Main:
    @cached_property
    def opts(self):
        parser = argparse.ArgumentParser(prog='dazl')
        parser.add_argument('--no-defaults',
                            action='store_true',
                            help='Do not include default values')
        parser.add_argument('--no-fallback',
                            action='store_true',
                            help='Do not include fallback values')
        parser.add_argument('-r', '--resolve-paths',
                            action='store_true',
                            help='Resolve all paths to absolute paths')
        parser.add_argument('-g', '--git-commit',
                            help='Git reference to use instead of currently checkout')
        parser.add_argument('-f', '--root-toml-file',
                            help=f"Path to the root TOML file (default '{DEFAULT_ROOT_TOML_FILE}'")

        subparsers = parser.add_subparsers(required=True, help='Subcommand')
        Component.register_subparser(subparsers)

        argcomplete.autocomplete(parser)

        return parser.parse_args(sys.argv[1:])

    @contextmanager
    def top_object(self):
        with TopObject._get_top_object(root_toml_file=self.opts.root_toml_file,
                                       commit=self.opts.git_commit,
                                       no_defaults=self.opts.no_defaults,
                                       no_fallback=self.opts.no_fallback,
                                       resolve_paths=self.opts.resolve_paths) as top_object:
            yield top_object

    def run(self):
        try:
            with self.top_object() as top_object:
                self.opts.cls(top_object=top_object, **vars(self.opts)).run()
        except FileNotFoundError as fnfe:
            print(fnfe)
            return -1
