from datetime import datetime
from typing import Any, Union, Literal

from pydantic import (
    BaseModel,
    NaiveDatetime,
    model_validator,
)

from .date import DateWithZone


class Event(BaseModel):
    uuid: str
    account: str
    application: str
    type: str
    name: str
    description: str
    timestamp: DateWithZone
    real_time: bool
    synced: NaiveDatetime
    additional: Union[str, bytes]
    additional_type: Literal["text", "bytes", "yaml", "json"]

    # todo(lalomartins): needs constructor

    @model_validator(mode="before")
    @classmethod
    def upgrade_json(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = data.copy()
            if "timezone" in new_data:
                new_data["timestamp"] = [
                    new_data["timestamp"][0] + new_data["timestamp"][1] / 1000000,
                    new_data["timezone"]["name"],
                ]
                del new_data["timezone"]
            if isinstance(new_data["synced"], list):
                new_data["synced"] = datetime.fromtimestamp(
                    new_data["synced"][0] + new_data["synced"][1] / 1000000
                ).isoformat()
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
        return data


sample_old_json = """{
    "uuid": "4+WBMKq3Ee6V23cA827xLQ==",
    "account": "bGFsby5tYXJ0aW5zQGdtYWlsLmNvbQ==",
    "application": "lalomartins.info/apps/weekly-goals",
    "type": "weekly goals",
    "name": "game dev",
    "description": "bevy PoC",
    "timestamp": [1704341725, 0],
    "timezone": {"name": "Asia/Tokyo", "offset": 0},
    "real_time": true,
    "synced": [1704589621, 943800],
    "additional": {"yaml": "foo: bar"}
}"""
sample = Event.model_validate_json(sample_old_json)
