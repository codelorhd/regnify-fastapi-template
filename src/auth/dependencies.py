"""Dependencies"""

from typing import List
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from jose import jwt, JWTError

from pydantic import ValidationError

from fastapi import Header, HTTPException, status, Depends, Security
from fastapi.security import SecurityScopes
from src.auth.exceptions import invalid_auth_credentials_exception
from src.auth.schemas import TokenData
from src.config import Settings
from src.database import get_db

from src.security import get_user, oauth2_scheme
from src.service import get_settings
from src.users.schemas import UserOut


def has_admin_token_in_header(admin_access_token: str = Header()):
    """Verifies if the header has an admin token"""

    if admin_access_token != "fake-super-secret-token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin-Access-Token header invalid",
        )


def verify_scope_permissions(
    token_data: TokenData, scopes: List[str], authenticate_value: str
):
    # * Allow the super admin to do everything!
    if token_data.is_super_admin:
        return

    for scope in scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )


def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    app_settings: Settings = Depends(get_settings),
):

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = invalid_auth_credentials_exception(authenticate_value)

    try:
        payload = jwt.decode(
            token=token,
            key=app_settings.secret_key,
            algorithms=[app_settings.algorithm],
        )
        email: str = payload.get("sub", None)  # type: ignore
        user_id: str = payload.get("id", None)  # type: ignore
        is_super_admin: bool = payload.get("is_super_admin", None)  # type: ignore

        if email is None or user_id is None or is_super_admin is None:
            raise credentials_exception

        token_scopes = payload.get("scopes", [])
        token_data = TokenData(
            id=UUID(user_id),
            is_super_admin=is_super_admin,
            email=email,
            scopes=token_scopes,
        )

    except (JWTError, ValidationError):
        raise credentials_exception

    user = get_user(db, username=token_data.email)
    if user is None:
        raise credentials_exception

    verify_scope_permissions(token_data, security_scopes.scopes, authenticate_value)

    return user


def get_current_active_user(
    current_user: UserOut = Security(get_current_user, scopes=["me"])
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return current_user


def user_must_be_admin(current_user: UserOut = Depends(get_current_user)):
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return current_user
