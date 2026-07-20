
import argcomplete
import argparse
import sys

from contextlib import contextmanager
from functools import cached_property

from .component import Component
from .model import Model
from .objects.top import TopObject


class Main:
    @cached_property
    def opts(self):
        parser = argparse.ArgumentParser(prog='dazl')
        parser.add_argument('--no-properties',
                            action='store_true',
                            help='Do not include property (dynamic key not in TOML) values')
        parser.add_argument('--no-fallback',
                            action='store_true',
                            help="Do not include fallback (values from 'groups') values")
        parser.add_argument('--no-defaults',
                            action='store_true',
                            help='Do not include default values')
        parser.add_argument('-f', '--root-toml-file',
                            help='Path to the root TOML file')

        subparsers = parser.add_subparsers(required=True, help='Subcommand')
        Component.register_subparser(subparsers)
        Model.register_subparser(subparsers)

        argcomplete.autocomplete(parser)

        return parser.parse_args(sys.argv[1:])

    @cached_property
    def top_object(self):
        return TopObject(root_toml_file=self.opts.root_toml_file,
                         no_properties=self.opts.no_properties,
                         no_fallback=self.opts.no_fallback,
                         no_defaults=self.opts.no_defaults)

    def run(self):
        try:
            return self.opts.cls(top_object=self.top_object, **vars(self.opts)).run()
        except FileNotFoundError as fnfe:
            print(fnfe)
            return -1
