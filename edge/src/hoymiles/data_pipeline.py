"""
Data Pipeline for processing and transforming sensor data

This module provides a flexible pipeline architecture for transforming
raw API data into sensor readings ready for MQTT publication.

Example usage:
    from data_pipeline import DataPipeline, DataTransformer

    class PowerTransformer(DataTransformer):
        def transform(self, data):
            data['real_power_kw'] = float(data['real_power']) / 1000
            return data

    pipeline = DataPipeline()
    pipeline.add_transformer(PowerTransformer())

    result = pipeline.execute({'real_power': 5000})
    # result = {'real_power': 5000, 'real_power_kw': 5.0}
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class DataTransformer(ABC):
    """
    Abstract base class for data transformers.

    Transformers process and modify data as it flows through the pipeline.
    Each transformer receives data and returns transformed data.
    """

    @abstractmethod
    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform the input data.

        Args:
            data: Input data dictionary

        Returns:
            Transformed data dictionary
        """

    def validate(self, data: dict[str, Any]) -> bool:
        """
        Validate that data is suitable for this transformer.

        Args:
            data: Input data dictionary

        Returns:
            True if data is valid, False otherwise
        """
        return True


class DataPipeline:
    """
    Data processing pipeline that chains multiple transformers.

    Data flows through transformers in order, allowing for
    composable and reusable transformations.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the data pipeline.

        Args:
            logger: Logger instance (optional)
        """
        self.transformers: list[DataTransformer] = []
        self.logger = logger or logging.getLogger(__name__)
        self.error_handlers: list[Callable[[Exception, dict[str, Any]], None]] = []

    def add_transformer(self, transformer: DataTransformer) -> "DataPipeline":
        """
        Add a transformer to the pipeline.

        Args:
            transformer: DataTransformer instance

        Returns:
            Self for method chaining
        """
        self.transformers.append(transformer)
        return self

    def add_error_handler(
        self, handler: Callable[[Exception, dict[str, Any]], None]
    ) -> "DataPipeline":
        """
        Add an error handler to the pipeline.

        Args:
            handler: Callable that receives (exception, data)

        Returns:
            Self for method chaining
        """
        self.error_handlers.append(handler)
        return self

    def execute(
        self, data: dict[str, Any], skip_on_error: bool = False
    ) -> dict[str, Any]:
        """
        Execute the pipeline with the given data.

        Args:
            data: Input data dictionary
            skip_on_error: If True, skip failed transformers instead of raising

        Returns:
            Transformed data dictionary

        Raises:
            Exception: If a transformer fails and skip_on_error is False
        """
        current_data = dict(data)  # Create a copy

        for transformer in self.transformers:
            try:
                if not transformer.validate(current_data):
                    self.logger.warning(
                        f"Transformer {transformer.__class__.__name__} validation failed"
                    )
                    if not skip_on_error:
                        raise ValueError(
                            f"Validation failed for {transformer.__class__.__name__}"
                        )
                    continue

                current_data = transformer.transform(current_data)
            except Exception as err:
                self.logger.error(f"Error in {transformer.__class__.__name__}: {err}")
                for handler in self.error_handlers:
                    try:
                        handler(err, current_data)
                    except Exception:
                        self.logger.exception("Error in error handler")
                if not skip_on_error:
                    raise

        return current_data

    def clear(self) -> None:
        """Remove all transformers from the pipeline."""
        self.transformers.clear()


# Built-in Transformers


class FilterKeysTransformer(DataTransformer):
    """
    Filter data to only include specified keys.

    Useful for removing internal fields or keeping only needed sensors.
    """

    def __init__(self, allowed_keys: list[str]):
        """
        Initialize the filter.

        Args:
            allowed_keys: List of keys to keep
        """
        self.allowed_keys = set(allowed_keys)

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Keep only allowed keys."""
        return {k: v for k, v in data.items() if k in self.allowed_keys}


class RenameKeysTransformer(DataTransformer):
    """Rename keys in the data dictionary."""

    def __init__(self, key_mapping: dict[str, str]):
        """
        Initialize the renamer.

        Args:
            key_mapping: Dictionary mapping old_key -> new_key
        """
        self.key_mapping = key_mapping

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Rename keys according to mapping."""
        result = dict(data)
        for old_key, new_key in self.key_mapping.items():
            if old_key in result:
                result[new_key] = result.pop(old_key)
        return result


class TypeCastTransformer(DataTransformer):
    """
    Cast values to specified types.

    Example:
        TypeCastTransformer({"real_power": float, "count": int})
    """

    def __init__(self, type_map: dict[str, type]):
        """
        Initialize the type caster.

        Args:
            type_map: Dictionary mapping key -> type
        """
        self.type_map = type_map

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Cast values to specified types."""
        result = dict(data)
        for key, target_type in self.type_map.items():
            if key in result and result[key] is not None:
                try:
                    result[key] = target_type(result[key])
                except (ValueError, TypeError) as err:
                    raise ValueError(
                        f"Cannot cast {key} to {target_type.__name__}: {err}"
                    )
        return result


class ScaleTransformer(DataTransformer):
    """Scale numeric values by a multiplier."""

    def __init__(self, scale_map: dict[str, float]):
        """
        Initialize the scaler.

        Args:
            scale_map: Dictionary mapping key -> scale_factor
        """
        self.scale_map = scale_map

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Scale values according to mapping."""
        result = dict(data)
        for key, scale in self.scale_map.items():
            if key in result and isinstance(result[key], (int, float)):
                result[key] = result[key] * scale
        return result


class RoundTransformer(DataTransformer):
    """Round numeric values to specified decimal places."""

    def __init__(self, round_map: dict[str, int]):
        """
        Initialize the rounder.

        Args:
            round_map: Dictionary mapping key -> decimal_places
        """
        self.round_map = round_map

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Round values according to mapping."""
        result = dict(data)
        for key, decimals in self.round_map.items():
            if key in result and isinstance(result[key], (int, float)):
                result[key] = round(result[key], decimals)
        return result


class CalculatedFieldTransformer(DataTransformer):
    """
    Add calculated fields based on other fields.

    Example:
        CalculatedFieldTransformer({
            "power_kw": lambda d: d.get("power", 0) / 1000
        })
    """

    def __init__(self, calculations: dict[str, Callable[[dict[str, Any]], Any]]):
        """
        Initialize the calculator.

        Args:
            calculations: Dictionary mapping new_key -> lambda_function
        """
        self.calculations = calculations

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add calculated fields."""
        print(f"Calculating data: {data}")
        result = dict(data)
        for key, calc_func in self.calculations.items():
            try:
                result[key] = calc_func(data)
            except Exception as err:
                raise ValueError(f"Error calculating {key}: {err}")
        return result


class FilterNullTransformer(DataTransformer):
    """Remove null or empty values from data."""

    def __init__(self, keep_zero: bool = True):
        """
        Initialize the null filter.

        Args:
            keep_zero: If True, keep values that are 0 (only remove None/"")
        """
        self.keep_zero = keep_zero

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove null/empty values."""
        result = {}
        for key, value in data.items():
            if value is None or value == "":
                continue
            if not self.keep_zero and value == 0:
                continue
            result[key] = value
        return result


class ConditionalTransformer(DataTransformer):
    """Apply transformations conditionally based on predicates."""

    def __init__(
        self,
        predicates: dict[str, Callable[[dict[str, Any]], bool]],
        transformations: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
    ):
        """
        Initialize the conditional transformer.

        Args:
            predicates: Dictionary mapping name -> predicate_function
            transformations: Dictionary mapping name -> transformation_function
        """
        self.predicates = predicates
        self.transformations = transformations

    def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply transformations if predicates match."""
        result = dict(data)
        for name, predicate in self.predicates.items():
            if predicate(result) and name in self.transformations:
                result = self.transformations[name](result)
        return result
