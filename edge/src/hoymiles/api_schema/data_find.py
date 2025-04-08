from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel


class DataFind(BaseModel):
    status: int
    message: str
    data: DataDict
    systemNotice: Optional[str] = None


class DataDict(BaseModel):
    mi_sn: Optional[int] = None
    net_state: int
    warn_list: Optional[list] = []
    dbg: bool
    warn_shield_set: Optional[List[WarnDict]] = []


class WarnDict(BaseModel):
    err_code: int
    start_at: datetime
    end_at: Optional[datetime | str] = "-"
    wdd1: str
    wd1: str
    wdd2: str
    wd2: str
