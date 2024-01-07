import base64
from pathlib import Path
from pydantic import UUID1

from .model.event import Event, sample


class Storage:
    application: str
    account: UUID1
    root: Path

    def __init__(self, application, account) -> None:
        self.application = application
        self.account = account
        self.path = Path(f"storage/{base64.encodebytes(account.encode("utf-8")).decode("ascii").strip()}/{application.replace("/", "-")}")
        print(self.path)

    def is_empty(self) -> bool:
        return not self.path.exists()

    def find_event(self, id) -> Event:
        if self.is_empty():
            raise KeyError(id)
        if (
            id == sample.uuid
            and self.application == sample.application
            and self.account == sample.account
        ):
            return sample
        raise KeyError(id)
