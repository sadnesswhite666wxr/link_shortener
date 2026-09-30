from sqlmodel import SQLModel


class AccessToken(SQLModel):
    access_token: str
    token_type: str
