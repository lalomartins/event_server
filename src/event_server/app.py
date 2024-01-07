from typing import Annotated, Union

from fastapi import FastAPI, HTTPException, Header
from pydantic import UUID1

from .model.event import Event, sample

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/events/{item_id}")
def read_item(
    item_id: UUID1,
    application: Annotated[str | None, Header(alias="x-application")] = None,
    account: Annotated[str | None, Header(alias="x-account")] = None,
):
    if (
        item_id == sample.uuid
        and application == sample.application
        and account == sample.account
    ):
        return sample
    raise HTTPException(status_code=404, detail="Item not found")
