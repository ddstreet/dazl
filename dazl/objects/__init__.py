
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
from functools import partial
from functools import singledispatchmethod
from glob import glob
from itertools import chain
from pathlib import Path
from types import SimpleNamespace


class FileBackedValue(ABC):
    @classmethod
    def _check_FBV(cls, value):
        if not isinstance(value, FileBackedValue):
            raise ValueError(f"Expected FileBackedValue type, got '{type(value).__name__}'")

    @classmethod
    def _FBV(cls, value, path):
        if isinstance(value, FileBackedValue):
            assert False # remove me!
            return value
        elif isinstance(value, dict):
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
    def _try_json(cls, value):
        try:
            return value._json
        except AttributeError:
            return value

    def __init__(self, fbv, *args, **kwargs):
        required_fbv_class = self._required_fbv_class()
        if not isinstance(fbv, required_fbv_class):
            raise TypeError(f"{self.__class__.__name__} value must be instance of {required_fbv_class.__name__}, got '{type(fbv).__name__}'")
        self.__fbv_containers = {}
        self.__fbv = fbv
        super().__init__(*args, **kwargs)
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

    @singledispatchmethod
    def _get_value(self, fbv, key):
        raise TypeError(f"{self.__name__} value must be instance of FileBackedValue, got '{type(fbv).__name__}'")

    @_get_value.register
    def _(self, fbv: FileBackedValue, key):
        return fbv.value

    @_get_value.register
    def _(self, fbd: FileBackedDict, key):
        return self._get_fbv_container(fbd, key, self._get_object_class)

    @_get_value.register
    def _(self, fbl: FileBackedList, key):
        return self._get_fbv_container(fbl, key, self._get_list_class)

    def _get_fbv_container(self, fbv, key, get_class):
        fbvid = id(fbv)
        if fbvid not in self.__fbv_containers:
            cls = get_class(fbv, key)
            self.__fbv_containers[fbvid] = cls(fbv, parent=self)
        return self.__fbv_containers[fbvid]


class FBVObject(FBVContainer, ABC):
    _KEY_CLASSMAP = {}
    _KEY_DEFAULTS = {}
    _KEY_CONVERSIONS = {}

    @classmethod
    def _get_object_list_class(cls):
        """Return class that accepts a list and uses this class for
        all list values, e.g. [cls(), cls(), ...].
        """
        return partial(DazlObjectList, child_class=cls)

    @classmethod
    def _required_fbv_class(cls):
        return FileBackedDict

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
        while 'includes' in self:
            for path in self._get_value(self._fbv.pop('includes'), 'includes'):
                self._fbv.merge(tomllib.loads(path.read_text()), path)

        if not self._top_object._no_defaults:
            self._setup_defaults()

    def _setup_defaults(self):
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

    def __dir__(self):
        return list(self._fbv.keys()) + list(self.__defaults.keys())

    def __iter__(self):
        return iter(dir(self))

    def _values(self):
        return [getattr(self, k) for k in self]

    def _items(self):
        return {k: getattr(self, k) for k in self}

    def _get_value(self, fbv, key):
        # FIXME - rework _get_value to actually provide fbv.value, add different methds for use by __getattribute__() to provide simple value or FBVList/FBVDict
        value = super()._get_value(fbv, key)

        # FIXME - change class vars into methods so we can include common fields like includes
        key_conversions = dict(includes=[Conversions.to_list, Conversions.resolve_glob_paths],
                               **self._KEY_CONVERSIONS)
        try:
            conversions = key_conversions[key]
        except KeyError:
            pass
        else:
            if not isinstance(conversions, list):
                conversions = [conversions]
            for conversion in conversions:
                value = conversion(key, value, fbv)

        return value

    def _getattr(self, name, from_fbv=True, from_defaults=True):
        if from_fbv and name in self._fbv:
            return self._get_value(self._fbv[name], name)
        if from_defaults and name in self.__defaults:
            return self._get_value(self.__defaults[name], name)
        raise AttributeError(name)

    def __getattribute__(self, name):
        if not name.startswith('_'):
            with suppress(AttributeError):
                return self._getattr(name)
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            raise AttributeError(f"Class {self.__class__.__name__} does not allow setting attributes ('{name}')")
        super().__setattr__(name, value)


class FBVNamedObject(FBVObject):
    @classmethod
    def _get_named_object_list_class(cls):
        """Return class that accepts a dict and uses this class for
        all dict values and provides the corresponding key name as the
        name of each value, e.g. {name1: cls(), name2: cls(), ...}.
        """
        return partial(DazlNamedObjectCollection, child_class=cls)

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

    def __dir__(self):
        return super().__dir__() + list(chain.from_iterable(map(iter, self._fallback_list)))

    def __getattribute__(self, name):
        if not name.startswith('_'):
            with suppress(AttributeError):
                return self._getattr(name, from_defaults=False)
            for fallback in self._fallback_list:
                with suppress(AttributeError):
                    return fallback._getattr(name, from_defaults=False)
        return super().__getattribute__(name)


class FBVList(FBVContainer, Sequence):
    @classmethod
    def _required_fbv_class(cls):
        return FileBackedList

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
        super().__init__(*args, **kwargs)

    @property
    def _parent(self):
        return self.__parent

    @property
    def _top_object(self):
        return self._parent._top_object

    @property
    def _top_dir(self):
        return self._parent._top_dir


class FBVObjectCollection(FBVContainer):
    def __init__(self, *args, child_class, **kwargs):
        self.__child_class = child_class
        super().__init__(*args, **kwargs)

    def _get_object_class(self, fbv, key):
        return self.__child_class


class FBVNamedObjectCollection(FBVObjectCollection):
    def __init__(self, *args, child_class, **kwargs):
        assert issubclass(child_class, FBVNamedObject)
        super().__init__(*args, child_class=child_class, **kwargs)

    def _get_object_class(self, fbv, key):
        return partial(super()._get_object_class(fbv, key), name=key)


class DazlObject(FBVChild, FBVObject):
    pass


class DazlList(FBVChild, FBVList):
    pass


class DazlObjectCollection(FBVObjectCollection, DazlList):
    pass


class DazlNamedObjectCollection(FBVNamedObjectCollection, DazlObject):
    pass


class NamedDazlObject(DazlObject, FBVNamedObject):
    pass


class TopDazlObject(FBVObject):
    def __init__(self, path, *args, no_defaults=False, resolve_paths=False, **kwargs):
        path = Path(path).resolve(strict=True)
        self.__no_defaults = no_defaults
        self.__resolve_paths = resolve_paths
        self.__top_dir = path.parent
        super().__init__(FileBackedDict(tomllib.loads(path.read_text()), path))

    @property
    def _no_defaults(self):
        return self.__no_defaults

    @property
    def _resolve_paths(self):
        return self.__resolve_paths

    @property
    def _top_object(self):
        return self

    @property
    def _top_dir(self):
        return self.__top_dir


class Conversions:
    @classmethod
    def to_list(cls, key, value, fbv):
        """If value is a string, return a list containing the string;
        if value is a list, return the value unchanged; if value is a
        FBVList, return a list of the FBVList's entries.
        """
        # FIXME - rework to only have simple values passed in, not FBVList
        if isinstance(value, FBVList):
            return value._fbv.value
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return value
        raise TypeError(f"Conversions.to_list requires value to be type str, list, or FBVList, got '{type(value).__name__}'")

    @classmethod
    def dashes_to_underscores(cls, key, value, fbv):
        """Return a string with all dashes in the value converted to
        underscores.
        """
        assert isinstance(value, str)
        return value.replace('-', '_')

    @classmethod
    def resolve_glob_paths(cls, key, value, fbv):
        """Return a list of absolute Paths resulting from applying
        globbing to the value, which must be a single (or list of)
        globbed string path(s) relative to the directory containing
        the fbv, and then resolving each Path.
        """
        if isinstance(value, str):
            value = [value]
        assert isinstance(value, list)
        return list(chain.from_iterable((cls._resolve_glob_path(path, fbv) for path in value)))

    @classmethod
    def _resolve_glob_path(cls, path, fbv):
        cls._check_not_absolute_path(path)
        for globbed_path in sorted(glob(path, root_dir=fbv.path_dir)):
            yield fbv.path_dir.joinpath(globbed_path).resolve(strict=True)

    @classmethod
    def _check_not_absolute_path(cls, path):
        if Path(path).is_absolute():
            raise ValueError(f"Path cannot be absolute: '{path}'")
