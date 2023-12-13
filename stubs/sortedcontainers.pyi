# https://pypi.org/project/sortedcontainers/
# https://github.com/grantjenks/python-sortedcontainers

from __future__ import annotations

from collections.abc import ItemsView, Iterable, Iterator, KeysView, MutableSequence, MutableSet, Sequence, ValuesView
from operator import eq, ge, gt, le, lt, ne
from typing import Any, Optional, Tuple, Union, overload

class SortedSet(MutableSet, Sequence):
    def __init__(self, iterable=None, key=None) -> None:
        ...

    @classmethod
    def _fromset(cls, values, key=None) -> SortedSet:
        ...

    @property
    def key(self) -> Any:
        ...

    def __contains__(self, value: Any) -> bool:
        ...

    @overload
    def __getitem__(self, index: int) -> Any:
        ...

    @overload
    def __getitem__(self, xxx: slice) -> Sequence[Any]:
        ...

    def __delitem__(self, index: int) -> None:
        ...

    def __make_cmp(set_op: Any, symbol: Any, doc: Any) -> Any:
        ...

    __eq__ = __make_cmp(eq, '==', 'equal to')
    __ne__ = __make_cmp(ne, '!=', 'not equal to')
    __lt__ = __make_cmp(lt, '<', 'a proper subset of')
    __gt__ = __make_cmp(gt, '>', 'a proper superset of')
    __le__ = __make_cmp(le, '<=', 'a subset of')
    __ge__ = __make_cmp(ge, '>=', 'a superset of')
    __make_cmp = staticmethod(__make_cmp)

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Any:
        ...

    def __reversed__(self) -> Iterator:
        ...

    def add(self, value: Any) -> None:
        ...

    def clear(self) -> None:
        ...

    def copy(self) -> SortedSet:
        ...

    def count(self, value: Any) -> int:
        ...

    def discard(self, value: Any) -> None:
        ...

    def pop(self, index: int = -1) -> Any:
        ...

    def remove(self, value: Any) -> None:
        ...

    def difference(self, *iterables: Any) -> SortedSet:
        ...

    def difference_update(self, *iterables: Any) -> SortedSet:
        ...

    def intersection(self, *iterables: Any) -> SortedSet:
        ...

    def intersection_update(self, *iterables: Any) -> SortedSet:
        ...

    __iand__ = intersection_update

    def symmetric_difference(self, other: Any) -> SortedSet:
        ...

    def symmetric_difference_update(self, other: Any) -> SortedSet:
        ...

    def union(self, *iterables: Any) -> SortedSet:
        ...

    def update(self, *iterables: Any) -> SortedSet:
        ...

    def __reduce__(self) -> Union[str, Tuple[Any, ...]]:
        ...

    def __repr__(self) -> str:
        ...

    def _check(self) -> None:
        ...


class SortedList(MutableSequence):
    def __init__(self, iterable: Any = None, key: Any = None) -> None:
        ...

    def __new__(cls, iterable: Any = None, key: Any = None) -> SortedList:
        ...

    @property
    def key(self) -> None:
        ...

    def _reset(self, load: Any) -> None:
        ...

    def clear(self) -> None:
        ...

    def add(self, value: Any) -> None:
        ...

    def _expand(self, pos: int):
        ...

    def update(self, iterable: Iterable):
        ...

    def __contains__(self, value: Any) -> bool:
        ...

    def discard(self, value: Any) -> None:
        ...

    def remove(self, value: Any) -> None:
        ...

    def _delete(self, pos: int, idx: int) -> None:
        ...

    def _loc(self, pos: int, idx: int) -> int:
        ...

    def _pos(self, idx: int) -> Tuple[int, int]:
        ...

    def _build_index(self) -> int:
        ...

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    @overload
    def __getitem__(self, index: int) -> Any:
        ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Any]:
        ...

    @overload
    def __setitem__(self, index: int, value: Any) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, values: Iterable[Any]) -> None:
        ...

    def __iter__(self) -> Iterator:
        ...

    def __reversed__(self) -> Iterator:
        ...

    def reverse(self) -> None:
        ...

    def islice(self, start: Optional[int] = None, stop: Optional[int] = None, reverse: bool = False) -> Iterator:
        ...

    def _islice(self, min_pos: int, min_idx: int, max_pos: int, max_idx: int, reverse: bool) -> Iterator:
        ...

    def irange(self, minimum: Optional[int] = None, maximum: Optional[int] = None, inclusive=(True, True),
               reverse: bool = False) -> Iterator:
        ...

    def __len__(self) -> int:
        ...

    def bisect_left(self, value: Any) -> int:
        ...

    def bisect_right(self, value: Any) -> int:
        ...

    def count(self, value: Any) -> int:
        ...

    def copy(self) -> SortedList:
        ...

    def append(self, value: Any) -> None:
        ...

    def extend(self, values: Any) -> None:
        ...

    def insert(self, index: int, value: Any) -> None:
        ...

    def pop(self, index: int = -1) -> Any:
        ...

    def index(self, value: Any, start: Optional[int] = None, stop: Optional[int] = None) -> int:
        ...

    def __add__(self, other: SortedList) -> SortedList:
        ...

    def __iadd__(self, other: Iterable[Any]) -> SortedList:
        ...

    def __mul__(self, num: int) -> SortedList:
        ...

    def __imul__(self, num: int) -> SortedList:
        ...

    def __reduce__(self) -> Any:
        ...

    def __repr__(self) -> str:
        ...

    def _check(self) -> None:
        ...


def identity(value: Any) -> Any:
    ...


class SortedKeyList(SortedList):
    """Sorted-key list is a subtype of sorted list.
    """
    def __init__(self, iterable: Optional[Iterable] = None, key: Any = identity) -> None:
        ...

    def __new__(cls, iterable: Optional[Iterable] = None, key: Any = identity) -> SortedKeyList:
        return object.__new__(cls)

    @property
    def key(self) -> Any:
        ...

    def clear(self) -> None:
        ...

    def add(self, value: Any) -> None:
        ...

    def _expand(self, pos: int) -> None:
        ...

    def update(self, iterable: Iterable) -> None:
        ...

    def __contains__(self, value: Any) -> bool:
        ...

    def discard(self, value: Any) -> None:
        ...

    def remove(self, value: Any) -> None:
        ...

    def _delete(self, pos: int, idx: int) -> None:
        ...

    def irange(self, minimum: Optional[int] = None, maximum: Optional[int] = None, inclusive=(True, True),
               reverse: bool = False) -> Iterator:
        ...

    def irange_key(self, min_key: Optional[Any] = None, max_key: Optional[Any] = None, inclusive=(True, True),
                   reverse: bool = False) -> Iterator:
        ...

    def bisect_left(self, value: Any) -> int:
        ...

    def bisect_right(self, value: Any) -> int:
        ...

    def bisect_key_left(self, key: Any) -> int:
        ...

    def bisect_key_right(self, key: Any) -> int:
        ...

    def count(self, value: Any) -> int:
        ...

    def copy(self) -> SortedKeyList:
        ...

    def index(self, value: Any, start: Optional[int] = None, stop: Optional[int] = None) -> int:
        ...

    def __add__(self, other: SortedList) -> SortedKeyList:
        ...

    def __mul__(self, num: int) -> SortedKeyList:
        ...

    def __reduce__(self) -> Any:
        ...

    def __repr__(self) -> str:
        ...

    def _check(self) -> None:
        ...


class SortedDict(dict):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...

    @property
    def key(self) -> Any:
        ...

    @property
    def iloc(self) -> Any:
        ...

    def clear(self) -> None:
        ...

    def __delitem__(self, key: Any) -> None:
        ...

    def __iter__(self) -> Iterator:
        ...

    def __reversed__(self) -> Iterator:
        ...

    def __setitem__(self, key: Any, value: Any) -> None:
        ...

    # @overload
    def __or__(self, other: Any) -> SortedDict:
        ...

    # @overload
    # def __or__(self, other: Iterable[Tuple[Any, Any]]) -> SortedDict:
    #     ...

    def __ror__(self, otherSortedDict) -> Any:
        ...

    # @overload
    def __ior__(self, other: Any) -> SortedDict:
        ...

    # @overload
    # def __ior__(self, other: Iterable[Tuple[Any, Any]]) -> SortedDict:
    #     ...

    def copy(self) -> SortedDict:
        ...

    @classmethod
    def fromkeys(cls, iterable: Iterable, value: Any = None) -> SortedDict:
        ...

    def keys(self) -> Any:
        ...

    def items(self) -> Any:
        ...

    def values(self) -> Any:
        ...

    class _NotGiven(object):
        # pylint: disable=too-few-public-methods
        def __repr__(self) -> str:
            ...

    @overload
    def pop(self, key: Any) -> Any:
        ...

    # @overload
    # def pop(self, key: Any, default: _NotGiven) -> _NotGiven:
    #     ...

    @overload
    def pop(self, key: Any, x: Union[Any, Any]) -> Union[Any, Any]:
        ...

    def popitem(self, index: int = -1) -> Any:
        ...

    def peekitem(self, index: int = -1) -> Any:
        ...

    def setdefault(self, key: Any, default: Any = None) -> Any:
        ...

    def update(self, *args: Any, **kwargs: Any) -> None:
        ...

    def __reduce__(self) -> Any:
        ...

    def __repr__(self) -> str:
        ...

    def _check(self) -> None:
        ...


def _view_delitem(self, index: Any) -> None:
    ...


class SortedKeysView(KeysView, Sequence):
    @classmethod
    def _from_iterable(cls, it: Iterable) -> SortedSet:
        ...

    @overload
    def __getitem__(self, index: int) -> Any:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Any]:
        ...


class SortedItemsView(ItemsView, Sequence):
    @classmethod
    def _from_iterable(cls, it: Iterable) -> SortedSet:
        ...

    @overload
    def __getitem__(self, index: int) -> Any:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Any]:
        ...


class SortedValuesView(ValuesView, Sequence):
    @overload
    def __getitem__(self, index: int) -> Any:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Any]:
        ...
