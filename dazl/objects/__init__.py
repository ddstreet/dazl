
import inspect
import json
import tomllib

from abc import ABC
from abc import abstractmethod
from collections.abc import MutableMapping
from collections.abc import MutableSequence
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass
from functools import cache
from functools import cached_property
from functools import singledispatchmethod
from glob import glob
from itertools import chain
from pathlib import Path
from types import SimpleNamespace


class FileBackedValue(ABC):
    @classmethod
    def _check_FBV(cls, value):
        assert isinstance(value, FileBackedValue), f"Expected FileBackedValue type, got '{type(value).__name__}'"

    @classmethod
    def _FBV(cls, value, path):
        assert not isinstance(value, FileBackedValue)
        if isinstance(value, dict):
            return FileBackedDict(value, path)
        elif isinstance(value, list):
            return FileBackedList(value, path)
        return FileBackedSimpleValue(value, path)

    @abstractmethod
    def _merge(self, value, path):
        pass

    def merge(self, value, path):
        if type(value) != type(self.value):
            raise ValueError(f"Can't merge 'type(value).__name__' type into 'type(self.value).__name__'")
        self._merge(value, path)

    @property
    @abstractmethod
    def value(self):
        pass

    @property
    @abstractmethod
    def path(self):
        pass

    @property
    def path_dir(self):
        return self.path.parent


class FileBackedSimpleValue(FileBackedValue):
    def __init__(self, value, path):
        self._history = []
        self._merge(value, path)

    def _merge(self, value, path):
        self._history.append((value, path))

    @property
    def value(self):
        return self._history[-1][0]

    @property
    def path(self):
        return self._history[-1][1]


class FileBackedList(FileBackedValue, MutableSequence):
    def __init__(self, sequence, path):
        self._path = path
        self._entries = []
        self.merge(sequence, path)

    def _merge(self, sequence, path):
        self._entries.extend([self._FBV(s, path) for s in sequence])

    def __getitem__(self, index):
        return self._entries[index]

    def __setitem__(self, index, value):
        self._check_FBV(value)
        self._entries[index] = value

    def __delitem__(self, index):
        del self._entries[index]

    def __len__(self):
        return len(self._entries)

    def insert(self, index, value, /):
        self._check_FBV(value)
        self._entries.insert(index, value)

    @property
    def value(self):
        return [e.value for e in self._entries]

    @property
    def path(self):
        # This provides the path where this list was *initially* defined
        return self._path


class FileBackedDict(FileBackedValue, MutableMapping):
    def __init__(self, mapping, path):
        self._path = path
        self._mapping = {}
        self.merge(mapping, path)

    def _convert_key(self, key):
        return key.replace('-', '_')

    def _merge(self, mapping, path):
        for k, v in mapping.items():
            k = self._convert_key(k)
            try:
                self[k].merge(v, path)
            except KeyError:
                self[k] = self._FBV(v, path)

    def __getitem__(self, key):
        return self._mapping[key]

    def __setitem__(self, key, value):
        self._check_FBV(value)
        self._mapping[key] = value

    def __delitem__(self, key):
        del self._mapping[key]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    @property
    def value(self):
        return {k: v.value for k, v in self._mapping.items()}

    @property
    def path(self):
        # This provides the path where this dict was *initially* defined
        return self._path


class FBVContainer(ABC):
    @classmethod
    @abstractmethod
    def _required_fbv_class(cls):
        pass

    @classmethod
    @abstractmethod
    def _get_default_value(cls):
        pass

    @classmethod
    def _try_json(cls, value):
        if hasattr(value, '_json'):
            return value._json
        return value

    def __init__(self, fbv, *args, **kwargs):
        required_fbv_class = self._required_fbv_class()
        assert isinstance(fbv, required_fbv_class), f"{self.__class__.__name__} value must be instance of {required_fbv_class.__name__}, got '{type(fbv).__name__}'"
        self.__fbv_containers = {}
        self.__fbv = fbv
        super().__init__()
        self._process()
        self._check()

    def _get_object_class(self, fbv, key):
        return DazlObject

    def _get_list_class(self, fbv, key):
        return DazlList

    @property
    @abstractmethod
    def _json(self):
        pass

    def __str__(self):
        return json.dumps(self._json, indent=2)

    @property
    def _fbv(self):
        return self.__fbv

    def _process(self):
        pass

    def _check(self):
        pass

    def _get_value(self, fbv, key):
        fbvid = id(fbv)
        if fbvid not in self.__fbv_containers:
            if isinstance(fbv, FileBackedDict):
                self.__fbv_containers[fbvid] = self._get_object_class(fbv, key)(fbv, parent=self, name=key)
            elif isinstance(fbv, FileBackedList):
                self.__fbv_containers[fbvid] = self._get_list_class(fbv, key)(fbv, parent=self, name=key)
            elif isinstance(fbv, FileBackedValue):
                return fbv.value
            else:
                raise TypeError(f"{self.__name__} value must be instance of FileBackedValue, got '{type(fbv).__name__}'")
        return self.__fbv_containers[fbvid]


class FBVObject(FBVContainer, ABC):
    _KEY_CLASSMAP = {}
    _KEY_DEFAULTS = {}
    _KEY_CONVERSIONS = {}
    _KEY_IGNORES = []

    @classmethod
    def _get_object_list_class(cls):
        """Return class that accepts a list and uses this class for
        all list values, e.g. [cls(), cls(), ...].
        """
        class DazlObjectCollection(DazlList):
            @classmethod
            def _get_obejct_class(innercls, fbv, key):
                return cls
        return DazlObjectCollection

    @classmethod
    def _required_fbv_class(cls):
        return FileBackedDict

    @classmethod
    def _get_default_value(cls):
        return {}

    def __init__(self, *args, **kwargs):
        self.__defaults = {}
        super().__init__(*args, **kwargs)

    def _get_object_class(self, fbv, key):
        try:
            return self._KEY_CLASSMAP[key]
        except KeyError:
            return super()._get_object_class(fbv, key)

    def _get_list_class(self, fbv, key):
        try:
            return self._KEY_CLASSMAP[key]
        except KeyError:
            return super()._get_list_class(fbv, key)

    @property
    def _json(self):
        return {k: self._try_json(getattr(self, k)) for k in self}

    def _process(self):
        while 'includes' in self._fbv:
            self._process_includes()

        if not self._config.no_defaults:
            self._setup_defaults()

    def _process_includes(self):
        includes = self._fbv.pop('includes')
        if isinstance(includes.value, str):
            self._process_include(includes.value, includes.path_dir)
        else:
            for include in includes:
                self._process_include(include.value, include.path_dir)

    def _process_include(self, include, path_dir):
        for path in self._resolve_relative_glob_paths(include, path_dir):
            self._fbv.merge(tomllib.loads(path.read_text()), path)

    def _resolve_relative_glob_paths(self, path, root_dir):
        if Path(path).is_absolute():
            raise ValueError(f"File path cannot be absolute: '{path}'")
        for p in sorted(glob(path, root_dir=root_dir)):
            newpath = root_dir.joinpath(p).resolve(strict=True)
            if not newpath.is_relative_to(self._top_dir):
                raise ValueError(f"File path '{newpath}' is above top dir '{self._top_dir}'")
            yield newpath

    def _setup_defaults(self):
        for k, cls in self._KEY_CLASSMAP.items():
            if k not in self._fbv:
                try:
                    value = self._KEY_DEFAULTS[k]
                except KeyError:
                    value = cls._get_default_value()
                self.__defaults[k] = FileBackedValue._FBV(value, self._fbv.path)

        for k, default in self._KEY_DEFAULTS.items():
            if k not in self._fbv:
                self.__defaults[k] = FileBackedValue._FBV(default, self._fbv.path)

    @property
    @abstractmethod
    def _top_object(self):
        pass

    @property
    @abstractmethod
    def _top_dir(self):
        pass

    @property
    def _iter_keys(self):
        for k in self._fbv.keys():
            yield k
        for k in self.__defaults.keys():
            yield k

    def __iter__(self):
        return (k for k in dict.fromkeys(self._iter_keys) if k not in self._KEY_IGNORES)

    def _values(self):
        return [getattr(self, k) for k in self]

    def _items(self):
        return {k: getattr(self, k) for k in self}

    def _get_value(self, fbv, key):
        value = super()._get_value(fbv, key)

        try:
            conversions = self._KEY_CONVERSIONS[key]
        except KeyError:
            pass
        else:
            if not isinstance(conversions, list):
                conversions = [conversions]
            for conversion in conversions:
                value = conversion(fbv, key, value)

        return value

    def __getattr__(self, name):
        if not name.startswith('_'):
            with suppress(KeyError):
                return self._get_value(self._fbv[name], name)
            with suppress(KeyError):
                return self._get_value(self.__defaults[name], name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            raise AttributeError(f"Class {self.__class__.__name__} does not allow setting attributes ('{name}')")
        super().__setattr__(name, value)


class FBVNamedObject(FBVObject):
    @classmethod
    def _get_named_object_collection_class(cls):
        """Return class that accepts a dict and uses this class for
        all dict values and provides the corresponding key name as the
        name of each value, e.g. {name1: cls(), name2: cls(), ...}.
        """
        class DazlNamedObjectCollection(DazlObject):
            @classmethod
            def _get_object_class(innercls, fbv, key):
                return cls
        return DazlNamedObjectCollection

    def __init__(self, *args, name, **kwargs):
        self.__name = name
        super().__init__(*args, **kwargs)

    @property
    def _name(self):
        return self.__name


class FBVFallbackObject(FBVObject, ABC):
    @property
    @abstractmethod
    def _fallback_list(self):
        pass

    @property
    def _iter_keys(self):
        for k in self._fbv.keys():
            yield k
        if not self._config.no_fallback:
            for fallback in self._fallback_list:
                for k in fallback._fbv.keys():
                    yield k
        for k in self.__defaults.keys():
            yield k

    def _getattr(self, name):
        if self._config.no_fallback:
            return super()._getattr(name)
        with suppress(KeyError):
            return self._get_value(self._fbv[name], name)
        for fallback in self._fallback_list:
            with suppress(KeyError):
                return fallback._get_value(fallback._fbv[name], name)
        with suppress(KeyError):
            return self._get_value(self.__defaults[name], name)
        raise AttributeError(name)


class FBVList(FBVContainer, Sequence):
    @classmethod
    def _required_fbv_class(cls):
        return FileBackedList

    @classmethod
    def _get_default_value(cls):
        return []

    @property
    def _json(self):
        return [self._try_json(e) for e in self]

    def __getitem__(self, index):
        return self._get_value(self._fbv[index], index)

    def __len__(self):
        return len(self._fbv)


class FBVChild:
    def __init__(self, *args, parent, **kwargs):
        self.__parent = parent
        self.__top_object = self.__parent._top_object
        super().__init__(*args, **kwargs)

    @property
    def _parent(self):
        return self.__parent

    @property
    def _top_object(self):
        return self.__top_object

    @property
    def _top_dir(self):
        return self.__top_object._top_dir

    @property
    def _config(self):
        return self.__top_object._config


class DazlObject(FBVChild, FBVObject):
    pass


class DazlList(FBVChild, FBVList):
    pass


class NamedDazlObject(DazlObject, FBVNamedObject):
    pass


class TopDazlObject(FBVObject):
    def __init__(self, path, *args, **kwargs):
        path = Path(path).resolve(strict=True)
        self.__config = Config(**kwargs)
        self.__top_dir = path.parent
        super().__init__(FileBackedDict(tomllib.loads(path.read_text()), path))

    @property
    def _top_object(self):
        return self

    @property
    def _top_dir(self):
        return self.__top_dir

    @property
    def _config(self):
        return self.__config


@dataclass
class Config:
    no_defaults: bool = False
    no_fallback: bool = False
    resolve_paths: bool = False


class Conversions:
    @classmethod
    def dashes_to_underscores(cls, fbv, key, value):
        return value.replace('-', '_')

    @classmethod
    def resolve_path(cls, fbv, key, value):
        if Path(value).is_absolute():
            raise ValueError(f"File path cannot be absolute: '{value}'")
        return fbv.path_dir.joinpath(value).resolve(strict=True)
