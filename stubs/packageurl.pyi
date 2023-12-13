# newer version have a py.typed file...

from collections import namedtuple
from typing import TYPE_CHECKING, Any, AnyStr, Dict, Optional, Tuple, Union

if TYPE_CHECKING:
    from collections.abc import Callable

# Python 3
basestring = (
    bytes,
    str,
)  # NOQA


def quote(s: AnyStr) -> str:
    ...


def unquote(s: AnyStr) -> str:
    ...


def get_quoter(encode: Optional[bool] = True,) -> "Union[Callable[[AnyStr], str], Callable[[str], str]]":
    ...


def normalize_type(type: Optional[AnyStr], encode: Optional[bool] = True) -> Optional[str]: ... # NOQA


def normalize_namespace(
    namespace: Optional[AnyStr], ptype: Optional[str], encode: Optional[bool] = True
) -> Optional[str]:  # NOQA
    ...


def normalize_name(
    name: Optional[AnyStr], ptype: Optional[str], encode: Optional[bool] = True
) -> Optional[str]:  # NOQA
    ...


def normalize_version(
    version: Optional[AnyStr], encode: Optional[bool] = True
) -> Optional[str]:  # NOQA
    ...


def normalize_qualifiers(
    qualifiers: Union[AnyStr, Dict[str, str], None], encode: Optional[bool] = True
) -> Union[str, Dict[str, str], None]:  # NOQA
    ...


def normalize_subpath(
    subpath: Optional[AnyStr], encode: Optional[bool] = True
) -> Optional[str]:  # NOQA
    ...


def normalize(
    type: Optional[AnyStr],
    namespace: Optional[AnyStr],
    name: Optional[AnyStr],
    version: Optional[AnyStr],
    qualifiers: Union[AnyStr, Dict[str, str], None],
    subpath: Optional[AnyStr],
    encode: Optional[bool] = True,
) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Union[str, Dict[str, str], None],
    Optional[str],
]:  # NOQA
    """
    Return normalized purl components
    """
    type_norm = normalize_type(type, encode)  # NOQA
    namespace_norm = normalize_namespace(namespace, type_norm, encode)
    name_norm = normalize_name(name, type_norm, encode)
    version_norm = normalize_version(version, encode)
    qualifiers_norm = normalize_qualifiers(qualifiers, encode)
    subpath_norm = normalize_subpath(subpath, encode)
    return type_norm, namespace_norm, name_norm, version_norm, qualifiers_norm, subpath_norm


class PackageURL(
    namedtuple("PackageURL", ("type", "namespace", "name", "version", "qualifiers", "subpath"))
):
    """
    A purl is a package URL as defined at
    https://github.com/package-url/purl-spec
    """

    name: str
    namespace: Optional[str]
    qualifiers: Union[str, Dict[str, str], None]
    subpath: Optional[str]
    type: str
    version: Optional[str]

    def __new__(
        self,
        type: Optional[AnyStr] = None,
        namespace: Optional[AnyStr] = None,
        name: Optional[AnyStr] = None,  # NOQA
        version: Optional[AnyStr] = None,
        qualifiers: Union[AnyStr, Dict[str, str], None] = None,
        subpath: Optional[AnyStr] = None,
    ) -> "PackageURL":  # this should be 'Self' https://github.com/python/mypy/pull/13133
        ...

    def __str__(self, *args: Any, **kwargs: Any) -> str:
        ...

    def __hash__(self) -> int:
        ...

    def to_dict(self, encode: Optional[bool] = False, empty: Any = None) -> Dict[str, Any]:
        ...

    def to_string(self) -> str:
        ...

    @classmethod
    def from_string(cls, purl: str) -> "PackageURL":
        ...
