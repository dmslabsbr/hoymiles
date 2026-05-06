"""
Refactored Hoymiles Application - Recommended Architecture

This is a complete example showing how to use the new modular architecture
to build a maintainable Hoymiles to MQTT integration.

Key improvements:
- Separated concerns: config, API, data transformation, MQTT publishing
- Centralized sensor definitions
- Composable data transformations
- Easy to extend with new sensors or data sources
- Better testability

Usage:
    python -m hoymiles.application

Configuration:
    Set environment variables or create config.json with:
    - HOYMILES_USER
    - HOYMILES_PASSWORD
    - HOYMILES_PLANT_ID
    - MQTT_HOST
    - MQTT_USER
    - MQTT_PASS
"""

import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .api_schema.station_select_device_of_tree import DevicedDict
from .cloud_api import CloudApi
from .config_manager import ConfigManager, load_config
from .data_pipeline import (
    CalculatedFieldTransformer,
    DataPipeline,
    FilterNullTransformer,
    RoundTransformer,
    TypeCastTransformer,
)
from .devices import BMS, Dtu, Micros
from .mqtt_publisher_hass import HAMQTTPublisher
from .sensor_registry import SensorRegistry

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("HoymilesApp")
root_logger = logging.getLogger()


class HoymilesApplication:
    """
    Main application for syncing Hoymiles data to Home Assistant via MQTT.
    """

    def __init__(self, config: ConfigManager):
        """
        Initialize the application.

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.logger = logging.getLogger("HoymilesApp.main")

        # Set log level for all loggers (root and application)
        log_level = config.get_str("LOG_LEVEL", "INFO")
        log_level_value = getattr(logging, log_level)
        print(f"Log level set to {log_level}")
        root_logger.setLevel(
            log_level_value
        )  # Set root logger so all modules inherit it
        logger.setLevel(log_level_value)

        # Initialize components
        self.sensor_registry = SensorRegistry()
        self.cloud_api = CloudApi(config)
        self.mqtt_publisher = HAMQTTPublisher(config, logger=logger)

        # State tracking
        self.is_running = False
        self.last_data_fetch = None
        self.last_hass_discovery = None
        self.last_token_refresh = None

        # Data pipelines
        self.plant_pipeline = self._create_plant_pipeline()

    def _create_plant_pipeline(self) -> DataPipeline:
        """Create data transformation pipeline for plant data."""
        pipeline = DataPipeline(logger=self.logger)

        # Add transformers in order
        pipeline.add_transformer(
            CalculatedFieldTransformer(
                {
                    "real_power_kw": lambda d: int(d.get("real_power", 0)) / 1000,
                    "array_size_kW": lambda d: int(d.get("array_size", 0)) / 1000,
                }
            )
        )

        pipeline.add_transformer(
            RoundTransformer(
                {
                    "real_power_kw": 3,
                    "array_size_kW": 3,
                    "co2_emission_reduction": 5,
                }
            )
        )

        pipeline.add_transformer(
            TypeCastTransformer(
                {
                    "real_power": float,
                    "today_eq": float,
                    "month_eq": float,
                    "year_eq": float,
                    "total_eq": float,
                }
            )
        )

        pipeline.add_transformer(FilterNullTransformer(keep_zero=True))

        return pipeline

    def start(self) -> None:
        """Start the application."""
        try:
            self.config.validate()
        except Exception as err:
            self.logger.error(f"Configuration error: {err}")
            raise

        self.logger.info("Starting Hoymiles Application")
        self.is_running = True

        # Get initial token before starting periodic data reads.
        if not self.cloud_api.get_token():
            self.logger.warning("Initial token fetch failed; will retry in main loop")
        else:
            self.last_token_refresh = datetime.now(tz=timezone.utc)

        # Start main loop in a thread
        loop_thread = threading.Thread(target=self._main_loop, daemon=True)
        loop_thread.start()

        self.logger.info("Application started. Press Ctrl+C to exit.")

        try:
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.stop()

    def stop(self) -> None:
        """Stop the application."""
        self.is_running = False
        self.mqtt_publisher.publish_availability("offline")
        self.mqtt_publisher.disconnect()
        self.logger.info("Application stopped")

    def _main_loop(self) -> None:
        """Main application loop."""
        get_data_interval = self.config.get_int("GET_DATA_INTERVAL", 480)
        hass_interval = self.config.get_int("HASS_INTERVAL", 300)
        auto_update_token = self.config.get_bool("AUTO_UPDATE_TOKEN", False)
        token_refresh_interval = self.config.get_int("TOKEN_REFRESH_INTERVAL", 72000)

        while self.is_running:
            try:
                now = datetime.now(tz=timezone.utc)

                # Publish Home Assistant discovery periodically
                if (
                    self.last_hass_discovery is None
                    or (now - self.last_hass_discovery).total_seconds() > hass_interval
                ):
                    self._publish_discovery()
                    self.last_hass_discovery = now

                # Fetch and publish data
                if (
                    self.last_data_fetch is None
                    or (now - self.last_data_fetch).total_seconds() > get_data_interval
                ):
                    self._fetch_and_publish_data()
                    self.last_data_fetch = now

                # Keep cloud token fresh in long-running sessions.
                if auto_update_token and (
                    self.last_token_refresh is None
                    or (now - self.last_token_refresh).total_seconds()
                    > token_refresh_interval
                ):
                    if self.cloud_api.get_token():
                        self.last_token_refresh = now
                    else:
                        self.logger.warning("Scheduled token refresh failed")

                time.sleep(10)  # Check every 10 seconds

            except Exception:
                self.logger.exception("Error in main loop")

    def _publish_discovery(self) -> None:
        """Publish Home Assistant discovery messages."""
        self.logger.info("Publishing Home Assistant discovery messages")

        plant_id = self.config.get_str("HOYMILES_PLANT_ID")

        try:
            # Get device hardware tree from API.
            devices_data = self.cloud_api.get_plant_hw(plant_id)

            if not devices_data:
                self.logger.warning("No device data received")
                return

            # Publish plant discovery
            self.mqtt_publisher.publish_discovery(
                device_type="plant",
                device_id=plant_id,
                device_name="Solar Plant",
                sensors=self.sensor_registry.get_sensors("plant"),
                device_info={"firmware_version": "1.0"},
            )

            # Parse and publish DTU/Micro/BMS discovery
            for device in devices_data:
                if device.get("type") == 1:  # DTU
                    dtu = Dtu(DevicedDict.model_validate(device))
                    self.mqtt_publisher.publish_discovery(
                        device_type="dtu",
                        device_id=dtu.id,
                        device_name=f"DTU {dtu.id}",
                        sensors=self.sensor_registry.get_sensors("dtu"),
                        device_info={
                            "model_no": dtu.model_no,
                            "firmware_version": dtu.soft_ver,
                        },
                    )

                for child in device.get("children", []):
                    if child.get("type") in (3, 6):  # Micro/Hybrid inverter
                        micro = Micros(DevicedDict.model_validate(child))
                        self.mqtt_publisher.publish_discovery(
                            device_type="micro",
                            device_id=micro.id,
                            device_name=f"Inverter {micro.id}",
                            sensors=self.sensor_registry.get_sensors("micro"),
                            device_info={
                                "model_no": micro.init_hard_no,
                                "firmware_version": micro.soft_ver,
                            },
                        )

                    for bms_child in child.get("children", []):
                        if bms_child.get("type") == 10:  # BMS
                            bms = BMS(DevicedDict.model_validate(bms_child))
                            self.mqtt_publisher.publish_discovery(
                                device_type="bms",
                                device_id=bms.id,
                                device_name=f"Battery {bms.id}",
                                sensors=self.sensor_registry.get_sensors("bms"),
                                device_info={
                                    "model": bms.model,
                                    "firmware_version": bms.soft_ver,
                                },
                            )

        except Exception:
            self.logger.exception("Error publishing discovery:")

    def _fetch_and_publish_data(self) -> None:
        """Fetch data from Hoymiles API and publish to MQTT."""
        self.logger.info("Fetching and publishing data")

        plant_id = self.config.get_str("HOYMILES_PLANT_ID")

        try:
            # Get solar data
            solar_data = self.cloud_api.get_solar_data(plant_id)

            if not solar_data:
                self.logger.warning("No solar data received")
                return

            # Transform data through pipeline
            transformed_data = self.plant_pipeline.execute(solar_data)

            # Publish plant data
            self.mqtt_publisher.publish_data(
                device_id=plant_id,
                data=transformed_data,
                include_timestamp=True,
            )

            self.logger.debug(f"Published plant data: {transformed_data}")

        except Exception:
            self.logger.exception("Error fetching/publishing data")

    def add_custom_sensor(
        self, device_type: str, sensor_key: str, sensor_def: Any
    ) -> None:
        """
        Add a custom sensor definition at runtime.

        Args:
            device_type: Type of device
            sensor_key: Unique sensor key
            sensor_def: SensorDefinition instance
        """
        self.sensor_registry.register_sensor(device_type, sensor_def)
        self.logger.info(f"Added custom sensor: {device_type}/{sensor_key}")

    def add_data_transformer(self, transformer: Any) -> None:
        """
        Add a custom data transformer to the plant pipeline.

        Args:
            transformer: DataTransformer instance
        """
        self.plant_pipeline.add_transformer(transformer)
        self.logger.info(f"Added transformer: {transformer.__class__.__name__}")


def main():
    """Main entry point."""
    # Load configuration from environment first, then optional file.
    config = load_config(logger=logger)

    config_file = os.getenv("HOYMILES_CONFIG_FILE", "")
    if config_file:
        config.load_from_file(config_file)
    else:
        for candidate in ("/data/options.json", "/config.json", "config.json"):
            if Path(candidate).exists():
                config.load_from_file(candidate)
                break

    # Create and start application
    app = HoymilesApplication(config)
    app.start()


if __name__ == "__main__":
    main()
