from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.exceptions import AuthError, ConflictError
from healthPilot.core.security import hash_password, verify_password
from healthPilot.models.enums import UserRole
from healthPilot.models.user import User
from healthPilot.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.settings = get_settings()

    async def register(self, name: str, email: str, password: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered", code="EMAIL_EXISTS")

        user = await self.users.create(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.user,
        )
        await self.session.commit()
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password", code="INVALID_CREDENTIALS")
        return user

    async def ensure_admin_exists(self) -> User | None:
        if await self.users.admin_exists():
            return None

        email = self.settings.ADMIN_EMAIL.strip()
        password = self.settings.ADMIN_PASSWORD
        if not email or not password:
            return None

        existing = await self.users.get_by_email(email)
        if existing:
            if existing.role != UserRole.admin:
                existing.role = UserRole.admin
                await self.session.commit()
            return existing

        admin = await self.users.create(
            name="Admin",
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
        )
        await self.session.commit()
        return admin
