
import argparse
import json
import sys

from contextlib import contextmanager
from contextlib import nullcontext
from functools import cached_property
from pathlib import Path

from .git import Git
from .exception import GitError
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
        parser.add_argument('-g', '--git-commit',
                            help='Git reference to use instead of currently checkout')
        parser.add_argument('-d', '--diff-from',
                            help='Show difference comparing from this git commit')
        parser.add_argument('-c', '--component',
                            action='append',
                            default=[],
                            help='Show only specified component(s)')
        parser.add_argument('root_toml_file',
                            nargs='?',
                            help='Path to the root TOML file')

        return parser.parse_args(sys.argv[1:])

    @cached_property
    def local_root_toml_file(self):
        if self.opts.root_toml_file:
            return Path(self.opts.root_toml_file)
        else:
            return Git().topleveldir / DEFAULT_ROOT_TOML_FILE

    @contextmanager
    def root_toml_file(self, commit=None):
        if not commit:
            commit = self.opts.git_commit

        if commit:
            with Git(self.local_root_toml_file).clone(commit) as clonefile:
                yield clonefile
        else:
            yield self.local_root_toml_file

    @contextmanager
    def top_object(self, commit=None):
        with self.root_toml_file(commit) as tomlfile:
            yield TopObject(tomlfile,
                            no_defaults=self.opts.no_defaults,
                            no_fallback=self.opts.no_fallback,
                            resolve_paths=self.opts.resolve_paths)

    def run(self):
        with self.top_object() as top:
            if self.opts.component:
                return self.print_components(top)
            else:
                return self.print_all(top)

    def components(self, top):
        components = (c.replace('-', '_') for c in self.opts.component)
        return {c: getattr(top.components, c)._json for c in components}

    def print_diff_from(self, top):
        with self.top_object(self.opts.diff_from) as top_from:
            print(DeepDiff(top_from._json, top._json, ignore_order=True))

    def print_components(self, top):
        try:
            components = self.components(top)
        except AttributeError as ae:
            print(f"Error getting component: {ae}")
            return -1

        if self.opts.diff_from:
            with self.top_object(self.opts.diff_from) as top_from:
                try:
                    components_from = self.components(top_from)
                except AttributeError as ae:
                    print(f"Error getting component: {ae}")
                    return -1

                from deepdiff import DeepDiff
                print(json.dumps(DeepDiff(components_from, components, ignore_order=True), indent=2))
        else:
            print(json.dumps(components, indent=2))

        return 0

    def print_all(self, top):
        if self.opts.diff_from:
            with self.top_object(self.opts.diff_from) as top_from:
                from deepdiff import DeepDiff
                print(json.dumps(DeepDiff(top_from._json, top._json, ignore_order=True), indent=2))
        else:
            print(top)

        return 0
