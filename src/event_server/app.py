import os
from typing import Annotated, List, Union

from fastapi import Body, FastAPI, HTTPException, Header, Query
from pydantic import UUID1, EmailStr

from event_server.basics import SimpleResponse

from .routes.auth import router as auth_router
from .model.date import NaiveDatetimeAsFloat
from .model.event import Event
from .storage import Storage


app = FastAPI()


app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/events")
def list_events(
    application: Annotated[str, Header(alias="x-application")],
    account: Annotated[EmailStr, Header(alias="x-account")],
    since: Annotated[
        NaiveDatetimeAsFloat | None,
        Query(description="Filter events synced since this timestamp"),
    ] = None,
    max: Annotated[int, Query(description="Maximum items to return")] = 100,
) -> List[Event]:
    storage = Storage(application=application, account=account)
    return storage.list(max=max, since=since)


@app.get("/events/{event_id}")
def read_event(
    event_id: UUID1,
    application: Annotated[str, Header(alias="x-application")],
    account: Annotated[EmailStr, Header(alias="x-account")],
) -> Event:
    storage = Storage(application=application, account=account)
    try:
        return storage.find_event(event_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")


@app.post("/events/")
def post_item(
    event: Annotated[Event, Body()],
    application: Annotated[str, Header(alias="x-application")],
    account: Annotated[EmailStr, Header(alias="x-account")],
) -> SimpleResponse:
    storage = Storage(application=application, account=account)
    return SimpleResponse()
