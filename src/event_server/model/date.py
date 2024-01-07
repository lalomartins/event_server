from datetime import datetime
from typing import Any
from typing_extensions import Annotated
from zoneinfo import ZoneInfo

from pydantic import (
    AwareDatetime,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapSerializer,
    WrapValidator,
)

utc = ZoneInfo("UTC")


def read_date_with_zone(
    v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
) -> datetime:
    if info.mode == "json":
        if isinstance(v, list):
            return datetime.fromtimestamp(v[0], tz=ZoneInfo(v[1]))
    return handler(v)


def ser_date_with_zone(v: datetime, nxt: SerializerFunctionWrapHandler) -> str:
    return nxt([v.timestamp(), v.tzinfo.key])


DateWithZone = Annotated[
    AwareDatetime,
    WrapValidator(read_date_with_zone),
    WrapSerializer(ser_date_with_zone, when_used="json"),
]
