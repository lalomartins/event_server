from typing import Union

from fastapi import FastAPI, HTTPException
from pydantic import UUID1

from .model.event import Event, sample

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/events/{item_id}")
def read_item(item_id: UUID1):
    if item_id == sample.uuid:
        return sample
    raise HTTPException(status_code=404, detail="Item not found")
