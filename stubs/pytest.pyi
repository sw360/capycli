# very simple stub for pytest

from typing import Any, Callable, Generator, Iterable, Optional, Pattern, Sequence, Tuple, Type, TypeVar, Union

# The value of the fixture -- return/yield of the fixture function (type variable).
FixtureValue = TypeVar("FixtureValue")

# The type of the fixture function (type variable).
FixtureFunction = TypeVar("FixtureFunction", bound=Callable[..., object])

# The type of a fixture function (type alias generic in fixture value).
_FixtureFunc = Union[
    Callable[..., FixtureValue], Callable[..., Generator[FixtureValue, None, None]]
]
# The type of FixtureDef.cached_result (type alias generic in fixture value).
_FixtureCachedResult = Union[
    Tuple[
        # The result.
        FixtureValue,
        # Cache key.
        object,
        None,
    ],
    Tuple[
        None,
        # Cache key.
        object,
        # Exception if raised.
        BaseException,
    ],
]


def fixture(  # noqa: F811
    fixture_function: None = ...,
    *,
    params: Optional[Iterable[object]] = ...,
    autouse: bool = ...,
    ids: Optional[
        Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]
    ] = ...,
    name: Optional[str] = None,
) -> FixtureFunction:  # type: ignore
    ...


class RaisesContext():
    def __enter__(self) -> Any:
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        ...

    ...


E = TypeVar("E", bound=BaseException)


def raises(
    expected_exception: Union[Type[E], Tuple[Type[E], ...]],
    *,
    match: Optional[Union[str, Pattern[str]]] = ...,
) -> "RaisesContext[E]":  # type: ignore
    ...
