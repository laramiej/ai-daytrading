"""
Authentication module for the AI Day Trading System
Provides JWT-based authentication for the web dashboard
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AuthManager:
    """Manages authentication for the trading dashboard"""

    def __init__(self, username: str, password: str, secret_key: str,
                 algorithm: str = "HS256", expiration_hours: int = 24):
        self.username = username
        self.password = password
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    def verify_credentials(self, username: str, password: str) -> bool:
        """Verify username and password"""
        return username == self.username and password == self.password

    def create_access_token(self) -> tuple[str, int]:
        """
        Create a JWT access token

        Returns:
            Tuple of (token, expires_in_seconds)
        """
        expires_delta = timedelta(hours=self.expiration_hours)
        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": self.username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        expires_in = int(expires_delta.total_seconds())

        return token, expires_in

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify a JWT token

        Args:
            token: JWT token string

        Returns:
            Username if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            if username is None:
                return None
            return username
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None


# Global auth manager instance (initialized in main.py)
auth_manager: Optional[AuthManager] = None


def init_auth_manager(settings) -> AuthManager:
    """Initialize the global auth manager with settings"""
    global auth_manager
    auth_manager = AuthManager(
        username=settings.auth_username,
        password=settings.auth_password,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expiration_hours=settings.jwt_expiration_hours
    )
    logger.info("Authentication manager initialized")
    return auth_manager


def get_auth_manager() -> AuthManager:
    """Get the global auth manager"""
    if auth_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured"
        )
    return auth_manager


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Dependency to get the current authenticated user

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    manager = get_auth_manager()
    username = manager.verify_token(credentials.credentials)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Dependency to optionally get the current user (for endpoints that work with or without auth)
    """
    if credentials is None:
        return None

    try:
        manager = get_auth_manager()
        return manager.verify_token(credentials.credentials)
    except HTTPException:
        return None
