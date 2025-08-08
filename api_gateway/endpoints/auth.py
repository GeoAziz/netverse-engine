# src/backend/api_gateway/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from pydantic import BaseModel
from typing import List

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthUser(BaseModel):
    uid: str
    email: str | None = None
    role: str = "viewer" # Default role

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    """
    Dependency to verify Firebase ID token and get user data including custom role.
    """
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        role = decoded_token.get("role", "viewer") # Default to 'viewer' if no role claim
        
        # On first login of a new user, assign them the 'analyst' role by default.
        # The very first user of the system should be made an admin manually or via a setup script.
        if "role" not in decoded_token:
            # Check if this is the first user ever
            users = auth.list_users().iterate_all()
            user_count = sum(1 for _ in users)
            
            # Reset the iterator for the actual assignment
            all_users = list(auth.list_users().iterate_all())

            if len(all_users) == 1:
                # This is the very first user, make them an admin
                new_role = "admin"
                auth.set_custom_user_claims(decoded_token['uid'], {'role': new_role})
                role = new_role
                print(f"First user {decoded_token.get('email')} automatically promoted to admin.")
            else:
                 # It's a new user but not the first, default to analyst
                new_role = "analyst"
                auth.set_custom_user_claims(decoded_token['uid'], {'role': new_role})
                role = new_role
                print(f"New user {decoded_token.get('email')} assigned default role of analyst.")


        return AuthUser(uid=decoded_token['uid'], email=decoded_token.get('email'), role=role)
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please reauthenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during authentication: {e}",
        )



def require_role(required_roles: List[str]):
    """Factory for creating a dependency that checks for a specific role."""
    async def role_checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required role. Required one of: {', '.join(required_roles)}.",
            )
        return current_user
    return role_checker

# Specific role dependencies for use in other endpoints
require_admin = require_role(["admin"])
require_analyst = require_role(["admin", "analyst"])
require_viewer = require_role(["admin", "analyst", "viewer"])


@router.get("/users/me", response_model=AuthUser)
async def read_users_me(current_user: AuthUser = Depends(get_current_user)):
    """
    A protected endpoint that returns the current authenticated user's details, including their role.
    """
    return current_user
