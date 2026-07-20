
import json

from .subcommand import SubCommand


class Model(SubCommand):
    @classmethod
    def command_name(cls):
        return 'model'

    @classmethod
    def command_help(cls):
        return 'Object Model JSON'

    @classmethod
    def add_parser_arguments(cls, subparser):
        subparser.add_argument('-j', '--jmespath',
                               help='Filter the output using JMESPath')
        super().add_parser_arguments(subparser)

    def __init__(self, *, jmespath, **kwargs):
        super().__init__(**kwargs)
        self.jmespath = jmespath

    def run(self):
        if self.jmespath:
            return self.show_object_model_jmespath_json()
        else:
            return self.show_object_model_full_json()

    def show_object_model_jmespath_json(self):
        try:
            import jmespath
        except ImportError as ie:
            print('Please install python3-jmespath')
            return -1

        print(json.dumps(jmespath.search(self.jmespath, self.top_object._json), indent=2))

    def show_object_model_full_json(self):
        print(json.dumps(self.top_object._json, indent=2))
