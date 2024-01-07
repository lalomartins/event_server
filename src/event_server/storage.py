import base64
from pathlib import Path
from pydantic import UUID1, ValidationError

from .model.event import Event


class Storage:
    application: str
    account: UUID1
    root: Path

    def __init__(self, application, account) -> None:
        self.application = application
        self.account = account
        self.path = Path(f"storage/{base64.standard_b64encode(account.encode("utf-8")).decode("ascii").strip()}/{application.replace("/", "-")}")
        print(self.path)

    def is_empty(self) -> bool:
        return not self.path.exists()

    def find_event(self, id) -> Event:
        if self.is_empty():
            raise KeyError(id)
        for year in self.path.iterdir():
            for json in year.glob("*.jsonl"):
                with open(json) as jf:
                    for line in jf.readlines():
                        try:
                            event = Event.model_validate_json(line)
                            if event.uuid == id:
                                return event
                        except ValidationError:
                            pass
        raise KeyError(id)
