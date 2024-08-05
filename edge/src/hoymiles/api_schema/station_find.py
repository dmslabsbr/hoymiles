from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StationFind(BaseModel):
    status: int
    message: str
    data: DataDict
    systemNotice: Optional[str] = None


class DataDict(BaseModel):
    id: int
    gid: int
    name: str
    type: int
    tz_id: int
    city_code: str
    status: int
    create_by: int
    create_at: datetime
    classify: int
    tz_name: str
    pic_path: str
    capacitor: str
    address: str
    layout_step: int
    is_balance: int
    is_reflux: int
    remarks: str
    config: dict
    is_stars: int
    money_unit: str
    electricity_price: float
    in_price: float
    usd: str
    nk_name: Optional[str] = None
    int5m: int
    city_id: int
    weather_of_cid: int
