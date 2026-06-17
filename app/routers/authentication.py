from fastapi import APIRouter, Request, HTTPException, Form
from typing import Dict, Any

from app.core import limiter
from app.core.services import authenticate_jira
from app.core.auth import create_access_token

router = APIRouter(prefix="/v1", tags=["Authentication"])

@router.post("/authentication", name="Authentication of user to the system")
async def authenticate(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
) -> Dict[str, Any]:
    """
    ## Authentication of user to the system
    
    ### Args:
    - **request: Request**: The request object.
    - **username: str**: The username of the user.
    - **password: str**: The password of the user.
    
    ### Returns:
    - **Dict[str, Any]**: Response status and message (HTTP 200 on success).
    
    ### Raises:
    - **HTTPException**: HTTP 401 if authentication fails, HTTP 500 on server error.
    """
    try:
        auth = authenticate_jira(username, password)
        
        if not auth:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed. Invalid username or password."
            )
        
        access_token = create_access_token(data={"sub": username})
        
        return {
            "response_status": "success",
            "message": "User authenticated successfully",
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))