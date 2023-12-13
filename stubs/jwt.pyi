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
    def sign(self, message: bytes, **options) -> bytes:
        ...

    @abstractmethod
    def verify(self, message: bytes, signature: bytes, **options) -> bool:
        ...

    @abstractmethod
    def to_dict(self, public_only: bool = True) -> Dict[str, str]:
        ...


class OctetJWK(AbstractJWKBase):

    def __init__(self, key: bytes, kid=None, **options) -> None:
        ...

        optnames = {'use', 'key_ops', 'alg', 'x5u', 'x5c', 'x5t', 'x5t#s256'}
        self.options = {k: v for k, v in options.items() if k in optnames}

    def get_kty(self):
        return 'oct'

    def get_kid(self):
        return self.kid

    def is_sign_key(self) -> bool:
        ...

    def _get_signer(self, options) -> Callable[[bytes, bytes], bytes]:
        ...

    def sign(self, message: bytes, **options) -> bytes:
        ...

    def verify(self, message: bytes, signature: bytes, **options) -> bool:
        ...

    def to_dict(self, public_only=True):
        ...

    @classmethod
    def from_dict(cls, dct):
        ...


class JWT:
    def __init__(self) -> None:
        ...

    def encode(self, payload: Dict[str, Any],
               key: Optional[AbstractJWKBase] = None, alg='HS256',
               optional_headers: Optional[Dict[str, str]] = None) -> str:
        ...

    def decode(self, message: str, key: Optional[AbstractJWKBase] = None,
               do_verify=True, algorithms: Optional[AbstractSet[str]] = None,
               do_time_check: bool = True) -> Dict[str, Any]:
        ...
