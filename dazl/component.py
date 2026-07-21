
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
        group = subparser.add_mutually_exclusive_group()
        group.add_argument('-d', '--diff-from',
                           help='Show difference comparing from this git commit')
        group.add_argument('--show-commits',
                           action='store_true',
                           help='Show all git commits (since the last update to the component dist-git dir) where this component was modified')

        subparser.add_argument('components',
                               nargs='+',
                               default=[],
                               help='Component name(s)')
        super().add_parser_arguments(subparser)

    def __init__(self, *, diff_from, show_commits, components, **kwargs):
        super().__init__(**kwargs)
        self.diff_from = diff_from
        self.show_commits = show_commits
        self.components = components

    def run(self):
        if self.diff_from:
            return self.run_show_diff()
        elif self.show_commits:
            return self.run_show_commits()
        else:
            return self.run_show_components()

    def run_show_diff(self):
        with self.top_object._get_top_object_at_commit(self.diff_from) as top_from:
            components_from = {k: v._json for k, v in top_from.components._items() if k in self.components}
            components_to = {k: v._json for k, v in self.top_object.components._items() if k in self.components}
            print(json.dumps(DeepDiff(components_from, components_to, ignore_order=True), indent=2))
        return 0

    def run_show_commits(self):
        for c in self.components:
            self.run_show_component_commits(c)
        return 0

    def run_show_component_commits(self, component):
        try:
            c = getattr(self.top_object.components, component)
        except AttributeError:
            print(f"Component '{component}' not found")
            return

        until = c.get_last_release_commit()
        self._run_show_component_commits(component, self.top_object, until)

    def _run_show_component_commits(self, component, top_object, until):
        previous_commit = top_object._git.get_hash_for_commit('HEAD^')
        current_commit = top_object._git.commit_hash

        print(f'checking {previous_commit}..{current_commit} until {until}')

        with top_object._get_top_object_at_commit(previous_commit) as previous_top_object:
            c1 = getattr(previous_top_object.components, component, None)
            c2 = getattr(top_object.components, component)
            if c1 != c2:
                print(top_object._git.commit_hash)
            if not c1 or previous_commit == until:
                return
            self._run_show_component_commits(component, previous_top_object, until)

    def run_show_components(self):
        components = {k: v._json for k, v in self.top_object.components._items() if k in self.components}
        missing = set(self.components) - set(components.keys())
        if missing:
            print(f"No component found for: {', '.join(missing)}")
            return -1

        print(json.dumps(components, indent=2))
        return 0

    def run_release(self):
        print('IMPLEMENT ME')
        return 0
