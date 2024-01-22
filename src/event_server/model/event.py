import base64
from typing import Annotated, Any, Optional, Union, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    model_validator,
)

from .date import DatetimeWithZone, NaiveDatetimeAsLong


class Event(BaseModel):
    uuid: UUID
    account: str
    application: str
    type: str
    name: str
    description: str
    timestamp: DatetimeWithZone
    real_time: bool
    synced: Optional[NaiveDatetimeAsLong]
    additional: Union[str, bytes]
    additional_type: Literal["text", "bytes", "yaml", "json"]

    @model_validator(mode="before")
    @classmethod
    def upgrade_json(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        new_data = data.copy()
        if len(new_data["account"]) and "@" not in new_data["account"]:
            new_data["uuid"] = base64.decodebytes(bytes(new_data["uuid"], "ascii"))
            new_data["account"] = base64.decodebytes(
                bytes(new_data["account"], "ascii")
            )
        # elif "-" in new_data["uuid"]:
        #     new_data["uuid"] = UUID(new_data["uuid"])
        if "timezone" in new_data:
            new_data["timestamp"] = (
                new_data["timestamp"][0],
                new_data["timezone"]["name"],
            )
            del new_data["timezone"]
        if isinstance(new_data["synced"], list):
            new_data["synced"] = new_data["synced"][0] * 1000000 + new_data["synced"][1]

        if isinstance(new_data["additional"], dict):
            additional = new_data["additional"]
            match (next(iter(additional.keys()))):
                case "str":
                    new_data["additional"] = additional["str"]
                    new_data["additional_type"] = "text"
                case "bytes":
                    new_data["additional"] = additional["bytes"]
                    new_data["additional_type"] = "bytes"
                case "yaml":
                    new_data["additional"] = additional["yaml"]
                    new_data["additional_type"] = "yaml"
        return new_data
