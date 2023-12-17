# newer version have a py.typed file...

from __future__ import annotations

from io import BufferedReader, BytesIO
from re import Pattern
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Sized,
    Tuple,
    Type,
    Union,
)

from requests.adapters import HTTPAdapter

# from urllib3.response import HTTPHeaderDict
from urllib3.response import HTTPResponse

if TYPE_CHECKING:  # pragma: no cover
    # import only for linter run
    import os
    from typing import Protocol

    from requests import PreparedRequest, models
    from urllib3 import Retry as _Retry

    class UnboundSend(Protocol):
        def __call__(
            self,
            adapter: HTTPAdapter,
            request: PreparedRequest,
            *args: Any,
            **kwargs: Any,
        ) -> models.Response:
            ...

    # Block of type annotations
    _Body = Union[str, BaseException, "Response", BufferedReader, bytes, None]
    _F = Callable[..., Any]
    _HeaderSet = Optional[Union[Mapping[str, str], List[Tuple[str, str]]]]
    _MatcherIterable = Iterable[Callable[..., Tuple[bool, str]]]
    _HTTPMethodOrResponse = Optional[Union[str, "BaseResponse"]]
    _URLPatternType = Union["Pattern[str]", str]
    _HTTPAdapterSend = Callable[
        [
            HTTPAdapter,
            PreparedRequest,
            bool,
            Union[float, Tuple[float, float], Tuple[float, None], None],
            Union[bool, str],
            Union[bytes, str, Tuple[Union[bytes, str], Union[bytes, str]], None],
            Optional[Mapping[str, str]],
        ],
        models.Response,
    ]


class Call(NamedTuple):
    ...


_real_send = HTTPAdapter.send
_UNSET = object()


class FalseBool:
    def __bool__(self) -> bool:
        ...


class FirstMatchRegistry:
    def __init__(self) -> None:
        ...

    @property
    def registered(self) -> List["BaseResponse"]:
        ...

    def reset(self) -> None:
        ...

    def find(
        self, request: "PreparedRequest"
    ) -> Tuple[Optional["BaseResponse"], List[str]]:
        ...

    def add(self, response: "BaseResponse") -> "BaseResponse":
        ...

    def remove(self, response: "BaseResponse") -> List["BaseResponse"]:
        ...

    def replace(self, response: "BaseResponse") -> "BaseResponse":
        ...


class OrderedRegistry(FirstMatchRegistry):
    def find(
        self, request: "PreparedRequest"
    ) -> Tuple[Optional["BaseResponse"], List[str]]:
        ...


def urlencoded_params_matcher(params: Optional[Dict[str, str]]) -> Callable[..., Any]:
    ...


def json_params_matcher(params: Optional[Dict[str, Any]]) -> Callable[..., Any]:
    ...


def _has_unicode(s: str) -> bool:
    ...


def _clean_unicode(url: str) -> str:
    ...


def get_wrapped(
    func: Callable[..., Any],
    responses: "RequestsMock",
    *,
    registry: Optional[Any] = None,
    assert_all_requests_are_fired: Optional[bool] = None,
) -> Callable[..., Any]:
    ...


class CallList(Sequence[Any], Sized):
    def __init__(self) -> None:
        ...

    def __iter__(self) -> Iterator[Call]:
        ...

    def __len__(self) -> int:
        ...

    def __getitem__(self, idx: Union[int, slice]) -> Union[Call, List[Call]]:
        ...

    def add(self, request: "PreparedRequest", response: "_Body") -> None:
        ...

    def add_call(self, call: Call) -> None:
        ...

    def reset(self) -> None:
        ...


def _ensure_url_default_path(
    url: "_URLPatternType",
) -> "_URLPatternType":
    ...


def _get_url_and_path(url: str) -> str:
    ...


class BaseResponse:
    passthrough: bool = False
    content_type: Optional[str] = None
    headers: Optional[Mapping[str, str]] = None
    stream: Optional[bool] = False

    def __init__(
        self,
        method: str,
        url: "_URLPatternType",
        match_querystring: Union[bool, object] = None,
        match: "_MatcherIterable" = (),
        *,
        passthrough: bool = False,
    ) -> None:
        ...

    def __eq__(self, other: Any) -> bool:
        ...

    def __ne__(self, other: Any) -> bool:
        ...

    def _should_match_querystring(
        self, match_querystring_argument: Union[bool, object]
    ) -> Union[bool, object]:
        ...

    def _url_matches(self, url: "_URLPatternType", other: str) -> bool:
        ...

    @staticmethod
    def _req_attr_matches(
        match: "_MatcherIterable", request: "PreparedRequest"
    ) -> Tuple[bool, str]:
        ...

    # def get_headers(self) -> HTTPHeaderDict:
    def get_headers(self) -> Any:
        ...

    def get_response(self, request: "PreparedRequest") -> HTTPResponse:
        ...

    def matches(self, request: "PreparedRequest") -> Tuple[bool, str]:
        ...

    @property
    def call_count(self) -> int:
        ...

    @property
    def calls(self) -> CallList:
        ...


def _form_response(
    body: Union[BufferedReader, BytesIO],
    headers: Optional[Mapping[str, str]],
    status: int,
) -> HTTPResponse:
    ...


class Response(BaseResponse):
    def __init__(
        self,
        method: str,
        url: "_URLPatternType",
        body: "_Body" = "",
        json: Optional[Any] = None,
        status: int = 200,
        headers: Optional[Mapping[str, str]] = None,
        stream: Optional[bool] = None,
        content_type: Union[str, object] = _UNSET,
        auto_calculate_content_length: bool = False,
        **kwargs: Any,
    ) -> None:
        ...

    def get_response(self, request: "PreparedRequest") -> HTTPResponse:
        ...

    def __repr__(self) -> str:
        ...


class CallbackResponse(BaseResponse):
    def __init__(
        self,
        method: str,
        url: "_URLPatternType",
        callback: Callable[[Any], Any],
        stream: Optional[bool] = None,
        content_type: Optional[str] = "text/plain",
        **kwargs: Any,
    ) -> None:
        ...

    def get_response(self, request: "PreparedRequest") -> HTTPResponse:
        ...


class PassthroughResponse(BaseResponse):
    def __init__(self, *args: Any, **kwargs: Any):
        ...


class RequestsMock:
    response_callback: Optional[Callable[[Any], Any]] = None

    def __init__(
        self,
        assert_all_requests_are_fired: bool = True,
        response_callback: Optional[Callable[[Any], Any]] = None,
        passthru_prefixes: Tuple[str, ...] = (),
        target: str = "requests.adapters.HTTPAdapter.send",
        registry: Type[FirstMatchRegistry] = FirstMatchRegistry,
        *,
        real_adapter_send: "_HTTPAdapterSend" = _real_send,
    ) -> None:
        ...

    def get_registry(self) -> FirstMatchRegistry:
        ...

    def _set_registry(self, new_registry: Type[FirstMatchRegistry]) -> None:
        ...

    def reset(self) -> None:
        ...

    def add(
        self,
        method: "_HTTPMethodOrResponse" = None,
        url: "Optional[_URLPatternType]" = None,
        body: "_Body" = "",
        adding_headers: "_HeaderSet" = None,
        *args: Any,
        **kwargs: Any,
    ) -> BaseResponse:
        ...

    def _parse_response_file(
        self, file_path: "Union[str, bytes, os.PathLike[Any]]"
    ) -> "Dict[str, Any]":
        ...

    def _add_from_file(self, file_path: "Union[str, bytes, os.PathLike[Any]]") -> None:
        ...

    def add_passthru(self, prefix: "_URLPatternType") -> None:
        ...

    def remove(
        self,
        method_or_response: "_HTTPMethodOrResponse" = None,
        url: "Optional[_URLPatternType]" = None,
    ) -> List[BaseResponse]:
        ...

    def replace(
        self,
        method_or_response: "_HTTPMethodOrResponse" = None,
        url: "Optional[_URLPatternType]" = None,
        body: "_Body" = "",
        *args: Any,
        **kwargs: Any,
    ) -> BaseResponse:
        ...

    def upsert(
        self,
        method_or_response: "_HTTPMethodOrResponse" = None,
        url: "Optional[_URLPatternType]" = None,
        body: "_Body" = "",
        *args: Any,
        **kwargs: Any,
    ) -> BaseResponse:
        ...

    def add_callback(
        self,
        method: str,
        url: "_URLPatternType",
        callback: Callable[
            ["PreparedRequest"],
            Union[Exception, Tuple[int, Mapping[str, str], "_Body"]],
        ],
        match_querystring: Union[bool, FalseBool] = FalseBool(),
        content_type: Optional[str] = "text/plain",
        match: "_MatcherIterable" = (),
    ) -> None:
        ...

    def registered(self) -> List["BaseResponse"]:
        ...

    @property
    def calls(self) -> CallList:
        ...

    def __enter__(self) -> "RequestsMock":
        ...

    def __exit__(self, type: Any, value: Any, traceback: Any) -> bool:
        ...

    def activate(
        self,
        func: Optional["_F"] = None,
        *,
        registry: Optional[Type[Any]] = None,
        assert_all_requests_are_fired: bool = False,
    ) -> Union[Callable[["_F"], "_F"], "_F"]:
        ...

    def _find_match(
        self, request: "PreparedRequest"
    ) -> Tuple[Optional["BaseResponse"], List[str]]:
        ...

    def _parse_request_params(
        self, url: str
    ) -> Dict[str, Union[str, int, float, List[Optional[Union[str, int, float]]]]]:
        ...

    def _on_request(
        self,
        adapter: "HTTPAdapter",
        request: "PreparedRequest",
        *,
        retries: Optional["_Retry"] = None,
        **kwargs: Any,
    ) -> "models.Response":
        ...

    def unbound_on_send(self) -> "UnboundSend":
        ...

    def start(self) -> None:
        ...

    def stop(self, allow_assert: bool = True) -> None:
        ...

    def assert_call_count(self, url: str, count: int) -> bool:
        ...


def __getattr__(name: str) -> Any:
    ...


def activate(func: _F = ...) -> _F:
    """Overload for scenario when 'responses.activate' is used."""
    ...
