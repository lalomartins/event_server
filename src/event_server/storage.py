import base64
from datetime import datetime
from logging import warn
from pathlib import Path
from typing import Union

from pydantic import UUID1, ValidationError

from .auth import AccountCredentials, AccountCredentialsSet
from .model.event import Event


class Storage:
    application: str
    account: UUID1
    root: Path

    def __init__(self, application, account) -> None:
        self.application = application
        self.account = account
        self.path = Path(f"storage/{base64.standard_b64encode(account.encode("utf-8")).decode("ascii").strip()}/{application.replace("/", "-")}")

    def is_empty(self) -> bool:
        return len(self.application) == 0 or not self.path.exists()

    def find_event(self, id) -> Event:
        if self.is_empty():
            raise KeyError(id)
        for year_partition in sorted(self.path.iterdir()):
            for day_partition in sorted(year_partition.glob("*.jsonl")):
                with day_partition.open() as jf:
                    for line in jf.readlines():
                        try:
                            event = Event.model_validate_json(line)
                            if event.uuid == id:
                                return event
                        except ValidationError:
                            pass
        raise KeyError(id)

    def list(self, max: int = 100, since: Union[datetime, None] = None):
        if len(self.application) == 0: return []

        events = []
        for year_partition in sorted(self.path.iterdir()):
            year = int(year_partition.name)
            if since is not None and since.year > year: continue
            for day_partition in sorted(year_partition.glob("*.jsonl")):
                is_since_day = False
                if since is not None and since.year == year:
                    month, day = map(int, day_partition.name.split(".")[0].split("-"))
                    if since.month > month or (since.month == month and since.day > day): continue
                    if since.month == month and since.day == day:
                        is_since_day = True
                with day_partition.open as jf:
                    for line in jf.readlines():
                        try:
                            event = Event.model_validate_json(line)
                            if (not is_since_day) or since < event.synced:
                                events.append(event)
                                if len(events) >= max:
                                    return events
                        except ValidationError:
                            warn("Validation error in storage, `%s` in %s", line, day_partition, exc_info=True)
        return events

    def add_credential(self, credential: AccountCredentials):
        credentials_file = self.path / "credentials.json"
        if credentials_file.exists():
            with open(credentials_file) as f:
                existing_credentials = AccountCredentialsSet.model_validate_json(f.read())
        else:
            existing_credentials = AccountCredentialsSet([])
        existing_credentials.root.append(credential)
        self.path.mkdir(parents=True, exist_ok=True)
        with open(credentials_file, "w") as f:
            f.write(existing_credentials.model_dump_json(indent=0))
