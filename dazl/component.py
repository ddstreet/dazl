
import json

from deepdiff import DeepDiff

from .exception import NoConfig
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
        group.add_argument('-r', '--render',
                           action='store_true',
                           help='Render to the local dist-git dir')
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

    def __init__(self, *, diff_from, show_commits, render, components, **kwargs):
        super().__init__(**kwargs)
        self.diff_from = diff_from
        self.show_commits = show_commits
        self.render = render
        self.components = components

    def get_components(self, top_object=None, raise_if_missing=True):
        top_object = top_object or self.top_object

        components = {c: getattr(top_object.components, c)
                      for c in self.components
                      if c in top_object.components}

        if raise_if_missing:
            missing = list(set(self.components) - set(components.keys()))
            if missing:
                raise NoConfig(f"Component(s) not found: {', '.join(missing)}")

        return components

    def get_component_plain_objects(self, components):
        return {k: v._json for k, v in components.items()}

    def run(self):
        try:
            components = self.get_components()
        except NoConfig as nc:
            print(nc)
            return -1

        if self.diff_from:
            return self.run_show_diff(components)
        elif self.show_commits:
            return self.run_show_commits(components)
        elif self.render:
            return self.run_release(components)
        else:
            return self.run_show_components(components)

    def run_show_diff(self, components):
        with self.top_object._get_top_object_at_commit(self.diff_from) as top_from:
            components_from = self.get_components(top_object=top_from, raise_if_missing=False)
            print(json.dumps(DeepDiff(self.get_component_plain_objects(components_from),
                                      self.get_component_plain_objects(components),
                                      ignore_order=True), indent=2))
        return 0

    def run_show_commits(self, components):
        for c in components.values():
            self.run_show_component_commits(c)
        return 0

    def run_show_component_commits(self, component):
        until = component.get_last_release_commit()
        self._run_show_component_commits(component, self.top_object, until)

    def _run_show_component_commits(self, component, top_object, until):
        previous_commit = top_object._git.get_hash_for_commit('HEAD^')
        current_commit = top_object._git.commit_hash

        print(f'checking {previous_commit}..{current_commit} until {until}')

        with top_object._get_top_object_at_commit(previous_commit) as previous_top_object:
            previous_component = getattr(previous_top_object.components, component._name, None)
            if previous_component != component:
                print(top_object._git.commit_hash)
            if not previous_component or previous_commit == until:
                return
            self._run_show_component_commits(previous_component, previous_top_object, until)

    def run_show_components(self, components):
        print(json.dumps(self.get_component_plain_objects(components), indent=2))
        return 0

    def run_release(self, components):
        for c in components.values():
            self.run_release_component(c)
        return 0

    def run_release_component(self, component):
        component.do_release()
