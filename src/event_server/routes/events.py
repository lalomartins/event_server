from typing import Annotated, List

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from pydantic import UUID1, EmailStr


from ..auth import Authentication, read_authentication
from ..basics import SimpleResponse
from ..model.date import NaiveDatetimeAsFloat
from ..model.event import Event
from ..storage import Storage

router = APIRouter(prefix="/auth")


@router.get("/events")
def list_events(
    application: Annotated[str, Header(alias="x-application")],
    auth: Annotated[Authentication, Depends(read_authentication)],
    since: Annotated[
        NaiveDatetimeAsFloat | None,
        Query(description="Filter events synced since this timestamp"),
    ] = None,
    max: Annotated[int, Query(description="Maximum items to return")] = 100,
) -> List[Event]:
    """Get all events synced after a certain timestamp"""
    storage = Storage(application=application, account=auth.account)
    return storage.list(max=max, since=since)


@router.get("/events/{event_id}")
def read_event(
    event_id: UUID1,
    application: Annotated[str, Header(alias="x-application")],
    auth: Annotated[Authentication, Depends(read_authentication)],
) -> Event:
    """Find a specific event by ID (slow)"""
    storage = Storage(application=application, account=auth.account)
    try:
        return storage.find_event(event_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/events/")
def post_item(
    event: Annotated[Event, Body()],
    application: Annotated[str, Header(alias="x-application")],
    auth: Annotated[Authentication, Depends(read_authentication)],
) -> Event:
    """Record a new event"""
    storage = Storage(application=application, account=auth.account)
    storage.add_event(event)
    return event
