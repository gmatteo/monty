"""
Useful collection classes, e.g., tree, frozendict, etc.
"""

from __future__ import annotations

import collections
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Iterable

    from typing_extensions import Self


def tree() -> collections.defaultdict:
    """
    A tree object, which is effectively a recursive defaultdict that
    adds tree as members.

    Usage:
        x = tree()
        x["a"]["b"]["c"] = 1

    Returns:
        A tree.
    """
    return collections.defaultdict(tree)


class frozendict(dict):
    """
    A dictionary that does not permit changes. The naming
    violates PEP 8 to be consistent with standard Python's "frozenset" naming.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        dict.__init__(self, *args, **kwargs)

    def __setitem__(self, key: Any, val: Any) -> None:
        raise KeyError(f"Cannot overwrite existing key: {str(key)}")

    def update(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        raise KeyError(f"Cannot update a {self.__class__.__name__}")


class Namespace(dict):
    """A dictionary that does not permit changing its values."""

    def __init__(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        self.update(*args, **kwargs)

    def __setitem__(self, key: Any, val: Any) -> None:
        if key in self:
            raise KeyError(f"Cannot overwrite existing key: {key!s}")

        dict.__setitem__(self, key, val)

    def update(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


class AttrDict(dict):
    """
    Allows to access values as dct.key in addition
    to the traditional way dct["key"]

    Examples:
        >>> dct = AttrDict(foo=1, bar=2)
        >>> assert dct["foo"] == dct.foo
        >>> dct.bar = "hello"
        >>> assert dct.bar == "hello"
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self) -> Self:
        """
        Returns:
            Copy of AttrDict
        """
        newd = super().copy()
        return self.__class__(**newd)


class FrozenAttrDict(frozendict):
    """
    A dictionary that:
        - Does not permit changes.
        - Allows to access values as dct.key in addition
          to the traditional way dct["key"]
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        super().__init__(*args, **kwargs)

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except KeyError as exc:
                raise AttributeError(str(exc))

    def __setattr__(self, name: str, value: Any) -> None:
        raise KeyError(
            f"You cannot modify attribute {name} of {self.__class__.__name__}"
        )


class MongoDict:
    """
    This dict-like object allows one to access the entries in a nested dict as
    attributes.
    Entries (attributes) cannot be modified. It also provides Ipython tab
    completion hence this object is particularly useful if you need to analyze
    a nested dict interactively (e.g. documents extracted from a MongoDB
    database).

    >>> m_dct = MongoDict({"a": {"b": 1}, "x": 2})
    >>> assert m_dct.a.b == 1 and m_dct.x == 2
    >>> assert "a" in m_dct and "b" in m_dct.a
    >>> m_dct["a"]
    {"b": 1}

    Notes:
        Cannot inherit from ABC collections.Mapping because otherwise
        dict.keys and dict.items will pollute the namespace.
        e.g MongoDict({"keys": 1}).keys would be the ABC dict method.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Args:
            args: Passthrough arguments for standard dict.
            kwargs: Passthrough keyword arguments for standard dict.
        """
        self.__dict__["_mongo_dict_"] = dict(*args, **kwargs)

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return str(self._mongo_dict_)

    def __setattr__(self, name: str, value: Any) -> None:
        raise NotImplementedError(
            f"You cannot modify attribute {name} of {self.__class__.__name__}"
        )

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            try:
                a = self._mongo_dict_[name]
                if isinstance(a, collections.abc.Mapping):
                    a = self.__class__(a)
                return a
            except Exception as exc:
                raise AttributeError(str(exc))

    def __getitem__(self, slice_) -> Any:
        return self._mongo_dict_.__getitem__(slice_)

    def __iter__(self) -> Iterable:
        return iter(self._mongo_dict_)

    def __len__(self) -> int:
        return len(self._mongo_dict_)

    def __dir__(self) -> list:
        """
        For Ipython tab completion.
        See http://ipython.org/ipython-doc/dev/config/integrating.html
        """
        return sorted(k for k in self._mongo_dict_ if not callable(k))


def dict2namedtuple(*args, **kwargs) -> tuple:
    """
    Helper function to create a class `namedtuple` from a dictionary.

    Examples:
        >>> tpl = dict2namedtuple(foo=1, bar="hello")
        >>> assert tpl.foo == 1 and tpl.bar == "hello"

        >>> tpl = dict2namedtuple([("foo", 1), ("bar", "hello")])
        >>> assert tpl[0] is tpl.foo and t[1] is tpl.bar

    Warnings:
        - The order of the items in the namedtuple is not deterministic if
          kwargs are used.
          namedtuples, however, should always be accessed by attribute hence
          this behaviour should not represent a serious problem.

        - Don't use this function in code in which memory and performance are
          crucial since a dict is needed to instantiate the tuple!
    """
    dct = collections.OrderedDict(*args)
    dct.update(**kwargs)
    return collections.namedtuple(
        typename="dict2namedtuple", field_names=list(dct.keys())
    )(**dct)
