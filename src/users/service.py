from uuid import UUID
from sqlalchemy.orm import Session
from src.config import Settings, setup_logger
from src.exceptions import BaseForbiddenException, GeneralException
from src.security import get_password_hash
from src.service import BaseService, ServiceResult

from src.users import schemas
from src.users.crud import UserCRUD
from src.users.exceptions import DuplicateUserException, UserNotFoundException
from src.users.models import User


class UserService(BaseService):
    def __init__(
        self, requesting_user: schemas.UserOut, db: Session, app_settings: Settings
    ) -> None:
        super().__init__(requesting_user, db)
        self.users_crud = UserCRUD(db)
        self.app_settings: Settings = app_settings
        self.logger = setup_logger()

        if requesting_user is None:
            raise GeneralException("Requesting User was not provided.")

    def update_user(self, id: UUID, user: schemas.UserUpdate) -> ServiceResult:
        try:
            if user.is_active is not None and not self.requesting_user.is_super_admin:
                return ServiceResult(
                    data=None,
                    success=False,
                    exception=BaseForbiddenException(
                        "You are not allowed to perform this action."
                    ),
                )

            updated_user = self.users_crud.update_user(id, user)
        except UserNotFoundException as raised_exception:
            return ServiceResult(data=None, success=False, exception=raised_exception)

        return ServiceResult(data=updated_user, success=True)

    def update_user_password(self, id: UUID, new_password: str) -> ServiceResult:
        hashed_password = get_password_hash(new_password)
        try:
            updated_user = self.users_crud.update_user_password(
                user_id=id, hashed_password=hashed_password
            )
        except UserNotFoundException as raised_exception:
            return ServiceResult(data=None, success=False, exception=raised_exception)

        return ServiceResult(data=updated_user, success=True)

    def create_user(
        self, user: schemas.UserCreate, admin_signup_token: str = None  # type: ignore
    ) -> ServiceResult:
        db_user: User = self.users_crud.get_user_by_email(email=user.email)
        if db_user:
            return ServiceResult(
                data=None,
                success=False,
                exception=DuplicateUserException(
                    f"The email is already registered. Try another one."
                ),
            )
        try:
            should_make_active = False
            if (
                admin_signup_token is not None
                and self.app_settings.admin_signup_token.lower()
                == admin_signup_token.lower()
            ):
                should_make_active = True
            else:
                user.is_super_admin = False

            created_user = self.users_crud.create_user(
                user, should_make_active, user.is_super_admin
            )
        except GeneralException as raised_exception:
            return ServiceResult(data=None, success=False, exception=raised_exception)

        return ServiceResult(data=created_user, success=True)

    def get_users(self, skip: int = 0, limit: int = 10) -> ServiceResult:
        db_users = self.users_crud.get_users(skip=skip, limit=limit)
        total_db_users = self.users_crud.get_total_users()

        users_data = {"total": total_db_users, "data": db_users}
        return ServiceResult(data=users_data, success=True)

    def get_user_by_id(self, id: UUID) -> ServiceResult:
        db_user: User = self.users_crud.get_user(id)  # type: ignore
        if not db_user:
            return ServiceResult(
                data=None,
                success=False,
                exception=UserNotFoundException(f"User with ID {id} not found"),
            )

        return ServiceResult(data=db_user, success=True)

    def get_user_by_email(self, email: str) -> ServiceResult:
        db_user: User = self.users_crud.get_user_by_email(email)  # type: ignore
        if not db_user:
            return ServiceResult(
                data=None,
                success=False,
                exception=UserNotFoundException(f"User with email {email} not found"),
            )

        return ServiceResult(data=db_user, success=True)

    def create_user_item(self, item: schemas.ItemCreate, user_id: int) -> ServiceResult:
        return ServiceResult(data=item, success=True)
