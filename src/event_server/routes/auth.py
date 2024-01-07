from typing import Annotated, Self

from fastapi import APIRouter, Body, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
import pyotp

from ..basics import SimpleResponse
from ..auth import AccountCredentials
from ..storage import Storage


router = APIRouter(prefix="/auth")


class AuthSettings:
    otp_issuer: str
    jwt_secret: str
    can_register: bool

    def load(self, source: dict) -> None:
        self.otp_issuer = source.get("EVENT_SERVER_OTP_ISSUER", "EventServer dev")
        self.jwt_secret = source.get("EVENT_SERVER_JWT_SECRET", "EventServer dev m0ck")
        match source.get("EVENT_SERVER_REGISTRATION_OPEN", "").lower():
            case "no" | "false" | "":
                self.can_register = False
            case _:
                self.can_register = True


settings = AuthSettings()


class RegistrationRequest(BaseModel):
    account: EmailStr
    password: str = Field(min_length=12)


class RegistrationResponse(SimpleResponse):
    otp_secret: str
    otp_uri: str

    @classmethod
    def from_totp(cls, totp: pyotp.TOTP) -> Self:
        return cls(
            otp_secret=totp.secret,
            otp_uri=totp.provisioning_uri(),
        )


@router.post("/register")
def register(
    credentials: Annotated[RegistrationRequest, Body()],
    application: Annotated[str, Header(alias="x-application")] = "",
) -> RegistrationResponse:
    """Register new credentials for an account"""
    storage = Storage(application=application, account=credentials.account)
    otp = pyotp.TOTP(
        pyotp.random_base32(),
        name=credentials.account,
        issuer=application or settings.otp_issuer,
    )
    storage.add_credential(
        AccountCredentials.create(
            otp_secret=otp.secret,
            password=credentials.password,
        )
    )
    return RegistrationResponse.from_totp(otp)


class LoginRequest(BaseModel):
    password: str = Field(min_length=12)
    otp: str = Field(min_length=6, max_length=6)


@router.post("/token-login")
def token_login(
    credentials: Annotated[LoginRequest, Body()],
    account: Annotated[EmailStr, Header(alias="x-account")],
    application: Annotated[str, Header(alias="x-application")] = "",
) -> str:
    storage = Storage(application=application, account=account)
    if storage.get_credentials().verify(credentials.password, credentials.otp):
        return "ok"
    else:
        raise HTTPException(status_code=401, detail="Bad credentials")
