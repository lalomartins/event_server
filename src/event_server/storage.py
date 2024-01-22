from abc import abstractmethod
import base64
from datetime import datetime, timedelta
import itertools
from logging import warn
from pathlib import Path
from typing import Optional, TextIO, Generator, Self, Union
from uuid import UUID
import zipfile

from pydantic import UUID1, ValidationError

from .auth import AccountCredentials, AccountCredentialsSet
from .model.event import Event


def zip_lt_monkeypatch(self: zipfile.Path, other: zipfile.Path):
    return self.filename < other.filename


zipfile.Path.__lt__ = zip_lt_monkeypatch


class DayPartition:
    month: int
    day: int
    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path
        self.month, self.day = map(int, path.stem.split("-"))

    def open(self) -> TextIO:
        return self.path.open()


class YearPartition:
    path: Path
    year: int

    def __init__(self, path) -> None:
        self.path = path
        self.year = int(path.name)

    def subpartitions(self) -> Generator[DayPartition, None, None]:
        for day_partition in sorted(self.path.glob("*.jsonl")):
            yield DayPartition(day_partition)

    @classmethod
    def all(cls, path: Path) -> Generator[Self, None, None]:
        for subpath in sorted(path.iterdir()):
            if subpath.is_dir():
                yield OpenYearPartition(subpath)
            if subpath.suffix == ".zip":
                try:
                    partition = ArchivedYearPartition(subpath)
                except TypeError:
                    pass
                else:
                    yield partition


class OpenYearPartition(YearPartition):
    @classmethod
    def all(cls, path: Path) -> Generator[Self, None, None]:
        for subpath in sorted(path.iterdir()):
            if subpath.is_dir():
                yield cls(subpath)


class ArchivedYearPartition(YearPartition):
    def __init__(self, path) -> None:
        self._path = path
        self.year = int(path.stem)
        self._zip = None

    @property
    def path(self):
        if self._zip is None:
            self._zip = zipfile.Path(zipfile.ZipFile(self._path))
            content = list(self._zip.iterdir())
            if len(content) == 1 and content[0].name == str(self.year):
                self._zip = zipfile.Path(
                    zipfile.ZipFile(self._path), at=f"{self.year}/"
                )

        return self._zip

    @classmethod
    def all(cls, path: Path) -> Generator[Self, None, None]:
        for zip in sorted(path.glob("*.zip")):
            try:
                partition = cls(zip)
            except TypeError:
                pass
            else:
                yield partition


class Storage:
    application: str
    account: UUID1
    root: Path

    def __init__(self, application, account) -> None:
        self.application = application
        self.account = account
        account_partition = (
            base64.standard_b64encode(account.encode("utf-8")).decode("ascii").strip()
        )
        application_partition = application.replace("/", "-")
        self.path = Path(f"storage/{account_partition}/{application_partition}")
        if len(self.application) == 0:
            self.user_storage = None
        else:
            self.user_storage = Storage("", account)

    def is_empty(self) -> bool:
        return len(self.application) == 0 or not self.path.exists()

    def find_event(self, id) -> Event:
        if self.is_empty():
            raise KeyError(id)
        for year_partition in YearPartition.all(self.path):
            for day_partition in year_partition.subpartitions():
                with day_partition.open() as jf:
                    for line in jf:
                        try:
                            event = Event.model_validate_json(line)
                            if event.uuid == id:
                                return event
                        except ValidationError:
                            pass
        raise KeyError(id)

    def list(self, max: int = 100, since: Optional[datetime] = None, after: Optional[UUID] = None):
        if len(self.application) == 0:
            return []

        if since is None:
            ref_date = datetime.fromtimestamp(0)
        else:
            ref_date = since - timedelta(days=1)
        after_matched = after is None

        events = []
        for year_partition in YearPartition.all(self.path):
            if ref_date.year > year_partition.year:
                continue

            for day_partition in year_partition.subpartitions():
                if ref_date.year == year_partition.year:
                    if ref_date.month > day_partition.month or (
                        ref_date.month == day_partition.month
                        and ref_date.day > day_partition.day
                    ):
                        continue
                with day_partition.open() as jf:
                    for line in jf:
                        try:
                            event = Event.model_validate_json(line)
                            if not after_matched:
                                if event.uuid == after:
                                    after_matched = True
                                continue
                            if after is not None or since is None or since <= event.synced:
                                events.append(event)
                                if len(events) >= max:
                                    return events
                        except ValidationError:
                            warn(
                                "Validation error in storage, `%s` in %s",
                                line,
                                day_partition.path,
                                exc_info=True,
                            )
        return events

    def add_event(self, event: Event):
        event.account = self.account
        event.application = self.application
        event.synced = datetime.now()
        day_partition = (
            self.path
            / str(event.synced.year)
            / f"{event.synced.month:02}-{event.synced.day:02}.jsonl"
        )
        day_partition.parent.mkdir(parents=True, exist_ok=True)
        with day_partition.open("a") as jf:
            jf.write(event.model_dump_json())
            jf.write("\n")

    def add_credential(self, credential: AccountCredentials):
        credentials_file = self.path / "credentials.json"
        if credentials_file.exists():
            with open(credentials_file) as f:
                existing_credentials = AccountCredentialsSet.model_validate_json(
                    f.read()
                )
        else:
            existing_credentials = AccountCredentialsSet([])
        existing_credentials.append(credential)
        self.path.mkdir(parents=True, exist_ok=True)
        with open(credentials_file, "w") as f:
            f.write(existing_credentials.model_dump_json(indent=0))

    def get_credentials(self):
        credentials_file = self.path / "credentials.json"
        if credentials_file.exists():
            with open(credentials_file) as f:
                credentials = AccountCredentialsSet.model_validate_json(f.read())
        else:
            credentials = AccountCredentialsSet([])
        if self.user_storage is not None:
            credentials.extend(self.user_storage.get_credentials())
        return credentials
