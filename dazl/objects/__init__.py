
import json
import tomllib

from collections.abc import Mapping
from collections.abc import MutableMapping
from functools import cached_property
from functools import singledispatchmethod
from glob import glob
from pathlib import Path
from types import SimpleNamespace

from .exception import NoParent
from .exception import NoParentAttribute


class TomlMap(MutableMapping):
    @classmethod
    def _json_encoder_default(cls, o):
        return o._toml_dict if isinstance(o, TomlMap) else o

    def __init__(self, toml_file, *, top_dir=None, toml_dict=None):
        self._toml_file = Path(toml_file).resolve(strict=True)
        self._top_dir = top_dir or self._toml_dir
        if not self._toml_file.is_relative_to(self._top_dir):
            raise ValueError(f"File path cannot be outside top-level dir '{self._top_dir}': '{self._toml_file}'")
        if not self._toml_file.exists():
            raise FileNotFoundError(f"File does not exist: '{self._toml_file}'")
        if toml_dict is None:
            toml_dict = tomllib.loads(self._toml_file.read_text())
        self._toml_dict = self._process_toml_dict(toml_dict)

    @cached_property
    def _toml_dir(self):
        return self._toml_file.parent

    def __str__(self):
        return json.dumps(self, indent=2, default=self._json_encoder_default)

    def __getitem__(self, key):
        return self._toml_dict[key]

    def __setitem__(self, key, value):
        self._toml_dict[key] = value

    def __delitem__(self, key):
        del self._toml_dict[key]

    def __iter__(self):
        return iter(self._toml_dict)

    def __len__(self):
        return len(self._toml_dict)

    def _process_toml_dict(self, toml_dict):
        return self._process_special_keys(self._process_items(toml_dict))

    def _process_items(self, toml_dict):
        return {self._process_key(k): self._process_value(v)
                for k, v in toml_dict.items()}

    def _process_key(self, key):
        return key.replace('-', '_')

    def _process_value(self, value):
        if isinstance(value, list):
            return [self._process_value(v) for v in value]
        if isinstance(value, dict):
            return TomlMap(self._toml_file, top_dir=self._top_dir, toml_dict=value)
        return value

    def _process_special_keys(self, toml_dict):
        return self._process_includes(toml_dict.get('includes'), toml_dict)

    def _process_includes(self, includes, toml_dict):
        if includes is None:
            return toml_dict
        if isinstance(includes, str):
            return self._process_includes([includes], toml_dict)
        if isinstance(includes, list):
            for include in includes:
                for path in self._resolve_relative_glob_paths(include):
                    self._merge_maps(toml_dict, TomlMap(path, top_dir=self._top_dir), insert_before_key='includes')
            toml_dict.pop('includes', None)
            return toml_dict
        raise TypeError(f"Invalid 'includes' value type '{type(includes).__name__}'")

    def _check_not_absolute_path(self, path):
        if Path(path).is_absolute():
            raise ValueError(f"File path cannot be absolute: '{path}'")

    def _resolve_relative_glob_paths(self, path):
        self._check_not_absolute_path(path)
        for globbed_subpath in sorted(glob(path, root_dir=self._toml_dir)):
            yield self._toml_dir / globbed_subpath

    def _resolve_relative_path(self, path):
        self._check_not_absolute_path(path)
        return self._toml_dir / path

    def _merge_maps(self, m1, m2, *, insert_before_key=None):
        for k, v2 in m2.items():
            try:
                v1 = m1[k]
            except KeyError:
                self._insert_key_before(m1, k, v2, insert_before_key)
            else:
                if type(v1) != type(v2):
                    raise ValueError(f"Type mismatch for key '{k}': {type(v1).__name__} != {type(v2).__name__}")
                m1[k] = self._merge_values(k, v1, v2)
        return m1

    def _merge_values(self, k, v1, v2):
        if isinstance(v1, list):
            return v1 + v2
        if isinstance(v1, Mapping):
            return self._merge_maps(v1, v2)
        return v2

    def _insert_key_before(self, m, key, value, insert_before_key):
        m[key] = value
        move = False
        for k in list(m.keys()):
            if k == insert_before_key:
                move = True
            if move:
                m[k] = m.pop(k)


class TomlObject(SimpleNamespace):
    _KEY_CLASSMAP = {}

    @classmethod
    def _get_instance_class(cls, key, value, *, parent, parent_attr=None):
        return cls

    @classmethod
    def _create_instance(cls, key, value, *, parent, parent_attr=None):
        if not isinstance(value, TomlMap):
            raise TypeError(f"TomlObject value must be instance of TomlMap, got '{type(value).__name__}'")
        cls = cls._get_instance_class(key, value, parent=parent, parent_attr=None)
        return cls(value, parent=parent, parent_attr=parent_attr)

    def __init__(self, toml_map, *, parent=None, parent_attr=None):
        assert isinstance(toml_map, TomlMap)
        self._toml_map = toml_map
        self.__parent = parent
        self.__parent_attr = parent_attr
        super().__init__(self._toml_map)
        for k, v in self._toml_map.items():
            self._process_item(k, v)
        self._check_instance()

    def _check_instance(self):
        pass

    @property
    def _parent(self):
        if self.__parent is None:
            raise NoParent(self)
        return self.__parent

    @property
    def _parent_attr(self):
        if self.__parent_attr is None:
            raise NoParentAttribute(self._parent, self)
        return self.__parent_attr

    def __str__(self):
        return str(self._toml_map)

    def __eq__(self, other):
        return all((isinstance(other, self.__class__),
                    self._eq_keys(other),
                    self._eq_values(other)))

    def _eq_keys(self, other):
        return vars(self).keys() == vars(other).keys()

    def _eq_values(self, other):
        return vars(self).values()

    def _get_value_class(self, key, value):
        if key in self._KEY_CLASSMAP:
            return self._KEY_CLASSMAP[key]
        if isinstance(value, TomlMap):
            return TomlObject
        return None

    def _get_value_instance(self, key, value):
        cls = self._get_value_class(key, value)
        if cls:
            if not issubclass(cls, TomlObject):
                raise TypeError(f"Value class must be subclass of TomlObject, got '{cls.__name__}'")
            return cls._create_instance(key, value, parent=self, parent_attr=key)
        return value

    def _process_item(self, key, value):
        if isinstance(value, list):
            new_value = [self._get_value_instance(None, v) for v in value]
        else:
            new_value = self._get_value_instance(key, value)
        if value != new_value:
            setattr(self, key, new_value)
