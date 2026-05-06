from __future__ import annotations

from pydantic import BaseModel


class DeviceTree(BaseModel):
    status: int
    message: str
    data: list[DevicedDict] | None = []
    systemNotice: str | None = None


class DevicedDict(BaseModel):
    id: int
    sn: str

    dtu_sn: str
    type: int
    model_no: str
    soft_ver: str
    hard_ver: str
    warn_data: WarnDict | dict | None = {}
    children: list[DevicedDict] | None = []


class WarnDict(BaseModel):
    connect: bool
    warn: bool
