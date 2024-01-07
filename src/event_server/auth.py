from datetime import datetime
import os
from typing import List
from argon2 import PasswordHasher

from pydantic import BaseModel, RootModel


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


AccountCredentialsSet = RootModel[List[AccountCredentials]]
