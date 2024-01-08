from __future__ import annotations
from datetime import datetime
import os
from typing import List, Self
from argon2 import PasswordHasher

from pydantic import BaseModel, Field, RootModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import pyotp


class AuthSettings(BaseSettings):
    otp_issuer: str = Field(default="EventServer dev")
    jwt_secret: str = Field(default="EventServer dev m0ck")
    registration_open: bool = Field(default=False)

    model_config = SettingsConfigDict(env_prefix="EVENT_SERVER_", env_file=".env")


settings = AuthSettings()


hasher = PasswordHasher()


class AccountCredentials(BaseModel):
    version: int
    otp_secret: str
    password_hash: bytes
    created: datetime

    @classmethod
    def create(cls, otp_secret: str, password: str):
        return cls(
            version=1,
            otp_secret=otp_secret,
            password_hash=hasher.hash(password),
            created=datetime.now(),
        )

    def verify(self, password: str, otp: str) -> bool:
        return hasher.verify(self.password_hash, password) and pyotp.TOTP(
            self.otp_secret
        ).verify(otp)


class AccountCredentialsSet(RootModel):
    root: List[AccountCredentials]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, index: int):
        return self.root[index]

    def append(self, item: AccountCredentials):
        self.root.append(item)

    def extend(self, other: Self):
        self.root.extend(other.root)

    def verify(self, password: str, otp: str) -> bool:
        for credential in self.root:
            if credential.verify(password, otp):
                return True
        return False
