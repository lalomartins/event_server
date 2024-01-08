from typing import Literal

from pydantic import BaseModel, Field

from .date import NaiveDatetimeAsFloat


class SimpleResponse(BaseModel):
    result: Literal["ok"] = Field(default="ok")


class CreatedResponse(SimpleResponse):
    id: str
    timestamp: NaiveDatetimeAsFloat
