from __future__ import annotations

from datetime import datetime, date
from logging import warn
from typing import Optional, List

from pydantic import BaseModel


class DeviceTree(BaseModel):
    status: int
    message: str
    data: Optional[List[DevicedDict]] = []
    systemNotice: Optional[str] = None


class DevicedDict(BaseModel):
    id: int
    sn: str

    dtu_sn: str
    type: int
    model_no: str
    soft_ver: str
    hard_ver: str
    warn_data: Optional[WarnDict | dict] = {}
    children: Optional[List[DevicedDict]] = []


class WarnDict(BaseModel):
    connect: bool
    warn: bool
