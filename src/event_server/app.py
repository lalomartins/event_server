from fastapi import FastAPI

from event_server.basics import SimpleResponse

from .routes.auth import router as auth_router
from .routes.events import router as events_router


app = FastAPI()


app.include_router(auth_router)
app.include_router(events_router)


@app.get("/")
def read_root():
    return SimpleResponse()
