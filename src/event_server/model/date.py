from datetime import datetime
from typing import Any, Tuple, Type, Union
from typing_extensions import Annotated
from zoneinfo import ZoneInfo

from pydantic import (
    AwareDatetime,
    GetCoreSchemaHandler,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapSerializer,
    WrapValidator,
)
from pydantic_core import CoreSchema, core_schema

utc = ZoneInfo("UTC")


class DatetimeWithZone(datetime):
    """
    DateTime which dumps as [timestamp, tzname]
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.tuple_positional_schema(
                [core_schema.float_schema(), core_schema.str_schema()]
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.serialize, when_used="json"
            ),
        )

    @classmethod
    def validate(cls, v: Tuple[float, str]):
        return datetime.fromtimestamp(v[0], tz=ZoneInfo(v[1]))

    @classmethod
    def serialize(cls, v: datetime, nxt: SerializerFunctionWrapHandler) -> str:
        return nxt((v.timestamp(), v.tzinfo.key))


class NaiveDatetimeAsFloat(datetime):
    """
    Naive DateTime which dumps as timestamp (float)
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.union_schema(
                [core_schema.float_schema(), core_schema.datetime_schema()]
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.serialize, when_used="json"
            ),
        )

    @classmethod
    def validate(cls, v: Union[float, datetime]):
        if isinstance(v, float):
            return datetime.fromtimestamp(v)
        return v

    @classmethod
    def serialize(cls, v: datetime, nxt: SerializerFunctionWrapHandler) -> str:
        return nxt(v.timestamp())
