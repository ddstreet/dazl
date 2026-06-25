
import argparse
import json
import sys

from functools import cached_property
from pathlib import Path

from .git import Git
from .objects.top import TopObject


DEFAULT_ROOT_TOML_FILE = "azldev.toml"


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
        parser.add_argument('-c', '--component',
                            action='append',
                            default=[],
                            help='Show only specified component(s)')
        parser.add_argument('root_toml_file',
                            nargs='?',
                            help='Path to the root TOML file')

        return parser.parse_args(sys.argv[1:])

    @cached_property
    def root_toml_file(self):
        return Path(self.opts.root_toml_file or f'{Git.toplevel()}/azldev.toml')

    def run(self):
        if not self.root_toml_file.exists():
            print(f"Root TOML file '{self.root_toml_file}' not found")
            return -1

        top_obj = TopObject(self.root_toml_file,
                            no_defaults=self.opts.no_defaults,
                            no_fallback=self.opts.no_fallback,
                            resolve_paths=self.opts.resolve_paths)

        if not self.opts.component:
            print(top_obj)
        else:
            components = {c: getattr(top_obj.components, c)._json for c in self.opts.component}
            print(json.dumps(components, indent=2))
            

        return 0
