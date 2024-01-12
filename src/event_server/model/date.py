from datetime import datetime, timedelta
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

    _epoch = datetime.fromtimestamp(0)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.tuple_positional_schema(
                [core_schema.int_schema(), core_schema.str_schema()]
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.serialize, when_used="json"
            ),
        )

    @classmethod
    def validate(cls, v: Tuple[int, str]):
        dt = cls._epoch + timedelta(seconds=v[0])
        return dt.replace(tzinfo=ZoneInfo(v[1]))

    @classmethod
    def serialize(cls, v: datetime, nxt: SerializerFunctionWrapHandler) -> str:
        delta = v.replace(tzinfo=None) - cls._epoch
        return nxt((int(delta.total_seconds()), v.tzinfo.key))


class NaiveDatetimeAsLong(datetime):
    """
    Naive DateTime which dumps as ns since epoch
    """

    _epoch = datetime.fromtimestamp(0)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Type[Any], handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.union_schema(
                [core_schema.int_schema(), core_schema.datetime_schema()]
            ),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls.serialize, when_used="json"
            ),
        )

    @classmethod
    def validate(cls, v: Union[int, datetime]):
        if isinstance(v, int) or isinstance(v, float):
            return cls._epoch + timedelta(microseconds=v)
        return v

    @classmethod
    def serialize(cls, v: datetime, nxt: SerializerFunctionWrapHandler) -> str:
        delta = v - cls._epoch
        return nxt(int(delta.total_seconds()) * 1000000 + delta.microseconds)
