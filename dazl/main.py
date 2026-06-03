
import argparse
import sys

from functools import cached_property
from pathlib import Path

from .objects.top import TopObject


DEFAULT_ROOT_TOML_FILE = "azldev.toml"


class Main:
    @cached_property
    def opts(self):
        parser = argparse.ArgumentParser(prog='dazl')
        parser.add_argument('root_toml_file',
                            nargs='?',
                            default=DEFAULT_ROOT_TOML_FILE,
                            help='Path to the root TOML file')

        return parser.parse_args(sys.argv[1:])

    @cached_property
    def root_toml_file(self):
        return Path(self.opts.root_toml_file)

    def run(self):
        if not self.root_toml_file.exists():
            print(f"Root TOML file '{self.root_toml_file}' not found")
            return -1

        top_obj = TopObject(self.root_toml_file)
        print(top_obj)

        return 0
