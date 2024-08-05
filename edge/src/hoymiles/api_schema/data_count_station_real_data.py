from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class DataCountStation(BaseModel):
    status: int
    message: str
    data: DataDict
    systemNotice: Optional[str] = None


class DataDict(BaseModel):
    today_eq: float
    month_eq: int
    year_eq: Optional[int] = None
    total_eq: int
    real_power: Optional[float] = None
    co2_emission_reduction: float
    plant_tree: int
    data_time: datetime
    last_data_time: datetime
    capacitor: float
    is_balance: int
    is_reflux: int
    reflux_station_data: Optional[RefluxDataDict] = None


class RefluxDataDict(BaseModel):
    start_date: Optional[datetime | str] = ""
    end_date: Optional[datetime | str] = ""

    pv_power: float
    grid_power: float
    load_power: float
    bms_power: float
    bms_soc: float

    bms_out_eq: float
    bms_in_eq: float

    mb_in_eq: MBOut
    mb_out_eq: MBIn


class MBOut(BaseModel):
    today_eq: float
    month_eq: float
    year_eq: float
    total_eq: float


class MBIn(BaseModel):
    today_eq: float
    month_eq: float
    year_eq: float
    total_eq: float
