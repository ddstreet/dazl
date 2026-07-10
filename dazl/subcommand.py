
from abc import ABC
from abc import abstractmethod


class SubCommand(ABC):
    @classmethod
    def register_subparser(cls, subparsers):
        subparser = subparsers.add_parser(cls.command_name(), help=cls.command_help())
        cls.add_parser_arguments(subparser)
        return subparser

    @classmethod
    @abstractmethod
    def command_name(cls):
        pass

    @classmethod
    @abstractmethod
    def command_help(cls):
        pass

    @classmethod
    def add_parser_arguments(cls, subparser):
        subparser.set_defaults(cls=cls)

    def __init__(self, *, top_object, **kwargs):
        self.top_object = top_object

    @abstractmethod
    def run(self):
        pass
