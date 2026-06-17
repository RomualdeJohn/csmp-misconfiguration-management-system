from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.logger import log
from app.core.clients import get_config 

config = get_config()
security = HTTPBearer()

JWT_SECRET_KEY = config['APP']['jwt_secret_key']
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = 24

def create_access_token(data: dict) -> str:
    """
    This function responsible for creating a JWT access token.
    
    Args:
        data: Dictionary containing data to encode in the token
    
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(hours=JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        log.warning(f"JWT token verification failed: {str(e)}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency function to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
    
    Returns:
        dict: Decoded token payload
    
    Raises:
        HTTPException: HTTP 401 if token is missing or invalid
    """
    token = credentials.credentials
    
    if not token:
        log.warning("Authentication token is missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(token)
    
    if payload is None:
        log.warning("Invalid or expired authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

