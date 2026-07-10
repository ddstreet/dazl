
import json

from deepdiff import DeepDiff

from .subcommand import SubCommand


class Component(SubCommand):
    @classmethod
    def command_name(cls):
        return 'component'

    @classmethod
    def command_help(cls):
        return 'Component operations'

    @classmethod
    def add_parser_arguments(cls, subparser):
        subparser.add_argument('-d', '--diff-from',
                               help='Show difference comparing from this git commit')
        subparser.add_argument('components',
                               nargs='+',
                               default=[],
                               help='Component name(s)')
        super().add_parser_arguments(subparser)

    def __init__(self, *, diff_from, components, **kwargs):
        super().__init__(**kwargs)
        self.diff_from = diff_from
        self.components = components

    def run(self):
        if self.diff_from:
            self.run_diff()
        else:
            self.run_show()

    def run_diff(self):
        with self.top_object._get_top_object_from_commit(self.diff_from) as top_from:
            components_from = {k: v._json for k, v in top_from.components._items() if k in self.components}
            components_to = {k: v._json for k, v in self.top_object.components._items() if k in self.components}
            print(json.dumps(DeepDiff(components_from, components_to, ignore_order=True), indent=2))

    def run_show(self):
        components = {k: v._json for k, v in self.top_object.components._items() if k in self.components}
        print(json.dumps(components, indent=2))

    def run_release(self):
        print('IMPLEMENT ME')
