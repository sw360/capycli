# https://github.com/GehirnInc/python-jwt

from abc import ABC, abstractmethod
from typing import AbstractSet, Any, Callable, Dict, Optional


class JWTException(Exception):
    """
    common base class for all exceptions used in python-jwt
    """


class MalformedJWKError(JWTException):
    ...


class UnsupportedKeyTypeError(JWTException):
    ...


class InvalidKeyTypeError(JWTException):
    ...


class JWSEncodeError(JWTException):
    ...


class JWSDecodeError(JWTException):
    ...


class JWTEncodeError(JWTException):
    ...


class JWTDecodeError(JWTException):
    ...


class AbstractJWKBase(ABC):
    @abstractmethod
    def get_kty(self) -> str:
        ...

    @abstractmethod
    def get_kid(self) -> str:
        ...

    @abstractmethod
    def is_sign_key(self) -> bool:
        ...

    @abstractmethod
    def sign(self, message: bytes, **options: Any) -> bytes:
        ...

    @abstractmethod
    def verify(self, message: bytes, signature: bytes, **options: Any) -> bool:
        ...

    @abstractmethod
    def to_dict(self, public_only: bool = True) -> Dict[str, str]:
        ...


class OctetJWK(AbstractJWKBase):

    def __init__(self, key: bytes, kid: Any = None, **options: Any) -> None:
        self.kid: Any
        ...

        optnames = {'use', 'key_ops', 'alg', 'x5u', 'x5c', 'x5t', 'x5t#s256'}
        self.options = {k: v for k, v in options.items() if k in optnames}

    def get_kty(self) -> Any:
        return 'oct'

    def get_kid(self) -> Any:
        return self.kid

    def is_sign_key(self) -> bool:
        ...

    def _get_signer(self, options: Any) -> Callable[[bytes, bytes], bytes]:
        ...

    def sign(self, message: bytes, **options: Any) -> bytes:
        ...

    def verify(self, message: bytes, signature: bytes, **options: Any) -> bool:
        ...

    def to_dict(self, public_only: bool = True) -> Any:
        ...

    @classmethod
    def from_dict(cls, dct: Any) -> None:
        ...


class JWT:
    def __init__(self) -> None:
        ...

    def encode(self, payload: Dict[str, Any],
               key: Optional[AbstractJWKBase] = None, alg: str = 'HS256',
               optional_headers: Optional[Dict[str, str]] = None) -> str:
        ...

    def decode(self, message: str, key: Optional[AbstractJWKBase] = None,
               do_verify: bool = True, algorithms: Optional[AbstractSet[str]] = None,
               do_time_check: bool = True) -> Dict[str, Any]:
        ...
