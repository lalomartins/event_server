from __future__ import annotations
from datetime import datetime
from logging import info
from typing import Annotated, List, Optional, Self

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field, RootModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import pyotp

JWT_ALGORITHM = "HS256"


class AuthSettings(BaseSettings):
    issuer: str = Field(default="EventServer dev")
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


def create_access_token(account: str, application: str):
    payload = {
        "sub": account,
        "iss": settings.issuer,
        "iat": datetime.now(),
    }
    if len(application) != 0:
        payload["aud"] = application

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )


class Authentication(BaseModel):
    account: str
    application: Optional[str]


bearer = HTTPBearer()


def read_authentication(
    token: Annotated[str, Depends(bearer)],
    application: Annotated[str, Header(alias="x-application")] = "",
):
    """Read and validate auth info from JWT in header"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token.credentials,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        account: str = payload.get("sub")
        auth_application: Optional[str] = payload.get("aud")
        if auth_application is not None and auth_application != application:
            raise credentials_exception
        if account is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return Authentication(account=account, application=auth_application)
