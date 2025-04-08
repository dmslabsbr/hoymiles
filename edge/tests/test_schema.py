import os

import pytest
import yaml
from hoymiles.api_schema.station_find import StationFind
from hoymiles.api_schema.data_count_station_real_data import DataCountStation
from hoymiles.api_schema.data_find import DataFind
from hoymiles.api_schema.station_select_device_of_tree import DeviceTree


class TestSchema:

    @pytest.mark.parametrize("file_name", [("1.json"), ("2.json"), ("3.json")])
    def test_station_find_schema(self, file_name: str):
        """Test is checking if schema is correctly parsing json data for station_find endpoint

        :param file_name: file name with json data
        :type file_name: str
        """
        file_path = os.path.join("tests", "resp_data", "station_find", file_name)
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            StationFind.model_validate(dict(data))

    @pytest.mark.parametrize(
        "file_name", [("1.json"), ("2.json"), ("3.json"), ("4.json")]
    )
    def test_data_count_station_real_data_schema(self, file_name: str):
        """Test is checking if schema is correctly parsing json data for data_count_station_real_data endpoint

        :param file_name: file name with json data
        :type file_name: str
        """
        file_path = os.path.join(
            "tests", "resp_data", "data_count_station_real_data", file_name
        )
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            DataCountStation.model_validate(dict(data))

    @pytest.mark.parametrize("file_name", [("1.json"), ("2.json")])
    def test_data_find_schema(self, file_name: str):
        """Test is checking if schema is correctly parsing json data for data_find_details endpoint

        :param file_name: file name with json data
        :type file_name: str
        """
        file_path = os.path.join("tests", "resp_data", "data_find_details", file_name)
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            DataFind.model_validate(dict(data))

    @pytest.mark.parametrize("file_name", [("1.json"), ("2.json"), ("3.json")])
    def test_data_find_schema(self, file_name: str):
        """Test is checking if schema is correctly parsing json data for station_select_device_of_tree endpoint

        :param file_name: file name with json data
        :type file_name: str
        """
        file_path = os.path.join(
            "tests", "resp_data", "station_select_device_of_tree", file_name
        )
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            DeviceTree.model_validate(dict(data))
