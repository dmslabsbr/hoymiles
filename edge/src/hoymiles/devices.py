from __future__ import annotations
import uuid
from .api_schema.station_select_device_of_tree import DevicedDict
from dataclasses import dataclass

"""
types:
1 - dtu/dtu_pro
3 - micro inverter
6 - hybrid inverter
10 - bms

"""


@dataclass(repr=True)
class DevData:
    connect: bool = False

    alarm_code: int = 0
    alarm_string: str = ""
    loading: bool = True


class PlantObject:
    """Generic class for devices in plant"""

    data = DevData()

    def __init__(self, data: DevicedDict) -> None:
        self.id = data.id  # pylint: disable=invalid-name
        self.sn = data.sn  # pylint: disable=invalid-name
        self.soft_ver = data.soft_ver
        self.hard_ver = data.hard_ver

        if data.warn_data and data.warn_data.connect:
            self.data.connect = data.warn_data.connect
        self.uuid = str(uuid.uuid1())
        self.err_code = 0
        self.err_msg = ""


class Dtu(PlantObject):
    """Class representig DTU device"""

    def __init__(self, dtu_data: DevicedDict) -> None:
        super(Dtu, self).__init__(dtu_data)
        self.model_no = dtu_data.model_no


class Micros(PlantObject):
    """Class representig Microinverter device"""

    data = DevData()

    def __init__(self, micro_data: DevicedDict) -> None:
        super(Micros, self).__init__(micro_data)
        self.init_hard_no = micro_data.model_no


class BMS(PlantObject):
    """Class representig Microinverter device"""

    data = DevData()

    def __init__(self, bms_data: DevicedDict) -> None:
        super(BMS, self).__init__(bms_data)
        self.model = "battery"
        self.reserve_soc = 30
        self.max_power = 80
