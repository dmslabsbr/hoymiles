"""
File contain dataclasses used in addon. Each data class represent part of payload send to cloud.

Here is example how to use it:

    from hoymiles.cloud_payloads import TokenBody, TokenPayload
    from dataclasses import asdict

    body = TokenBody("asxd", "asxd")
    payload = TokenPayload(body)
    print(asdict(payload))
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(repr=True)
class Body:
    pass


@dataclass(repr=True)
class LoadBody:
    loading: bool = True


@dataclass(repr=True)
class TokenPayload:
    body: TokenBody
    ERROR_BACK: bool = True
    LOAD: LoadBody = LoadBody()
    WAITING_PROMISE: bool = True


@dataclass(repr=True)
class TokenBody:
    password: str
    user_name: str


@dataclass(repr=True)
class SidBody:
    sid: str


@dataclass(repr=True)
class IdBody:
    id: str


@dataclass(repr=True)
class InverterBody:
    mi_id: str
    mi_sn: str
    time: str
    sid: str
    port: int = 1
    warn_code: int = 1
