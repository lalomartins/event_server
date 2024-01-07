from typing import Annotated, Union

from fastapi import FastAPI, HTTPException, Header
from pydantic import UUID1

from .model.event import Event, sample
from .storage import Storage

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/events/{event_id}")
def read_item(
    event_id: UUID1,
    application: Annotated[str | None, Header(alias="x-application")] = None,
    account: Annotated[str | None, Header(alias="x-account")] = None,
):
    storage = Storage(application=application, account=account)
    try:
        return storage.find_event(event_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")
