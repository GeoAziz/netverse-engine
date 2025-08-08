# src/backend/api_gateway/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, constr
from typing import List
from firebase_admin import auth

from .auth import require_admin, AuthUser

router = APIRouter()

class UserRecord(BaseModel):
    uid: str
    email: str | None = None
    role: str

class RoleAssignmentRequest(BaseModel):
    role: constr(pattern=r"^(admin|analyst|viewer)$") # Ensure role is one of the valid types

@router.get("/users", response_model=List[UserRecord], dependencies=[Depends(require_admin)])
async def list_all_users():
    """
    Lists all users in the Firebase project.
    Requires admin privileges.
    """
    try:
        users = auth.list_users().iterate_all()
        user_list = []
        for user in users:
            claims = user.custom_claims or {}
            user_list.append(UserRecord(
                uid=user.uid,
                email=user.email,
                role=claims.get("role", "viewer") # Default to viewer if no role set
            ))
        return user_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/users/{uid}/role", response_model=UserRecord, dependencies=[Depends(require_admin)])
async def assign_user_role(uid: str, request: RoleAssignmentRequest):
    """
    Assigns a role to a specific user by their UID.
    Requires admin privileges.
    """
    try:
        # Set the custom claim for the user
        auth.set_custom_user_claims(uid, {'role': request.role})
        
        # Retrieve the updated user record to confirm the change
        updated_user = auth.get_user(uid)
        updated_claims = updated_user.custom_claims or {}
        
        return UserRecord(
            uid=updated_user.uid,
            email=updated_user.email,
            role=updated_claims.get("role", "viewer")
        )
    except auth.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assign role: {e}")
