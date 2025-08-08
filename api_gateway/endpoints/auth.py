
# src/backend/api_gateway/endpoints/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth, firestore
from pydantic import BaseModel
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthUser(BaseModel):
    uid: str
    email: str | None = None
    role: str = "viewer" # Default role

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    """
    Dependency to verify Firebase ID token and get user data including custom role.
    Handles first-time login role assignment.
    """
    try:
        decoded_token = auth.verify_id_token(token, check_revoked=True)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        role = decoded_token.get("role", "viewer") 
        
        # If user has no role claim, it's their first login. Assign one.
        if "role" not in decoded_token:
            logger.info(f"No role found for user {email}. Assigning default role.")
            
            db = firestore.client()
            users_ref = db.collection("users")
            all_users_snapshot = list(users_ref.stream())

            # The very first user in the system gets to be admin
            if not all_users_snapshot or (len(all_users_snapshot) == 1 and all_users_snapshot[0].id == uid):
                new_role = "admin"
                logger.info(f"User {email} is the first user. Promoting to 'admin'.")
            else:
                new_role = "analyst"
                logger.info(f"Assigning new user {email} the default role of 'analyst'.")

            # Set the custom claim and update Firestore
            auth.set_custom_user_claims(uid, {'role': new_role})
            user_doc_ref = users_ref.document(uid)
            user_doc_ref.set({
                'uid': uid,
                'email': email,
                'role': new_role,
            }, merge=True)
            
            role = new_role

        return AuthUser(uid=uid, email=email, role=role)

    except auth.RevokedIdTokenError:
        logger.warning("Authentication failed: Token has been revoked.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please reauthenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        logger.warning("Authentication failed: Invalid ID token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during authentication: {e}",
        )


def require_role(required_roles: List[str]):
    """Factory for creating a dependency that checks for a specific role."""
    async def role_checker(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if current_user.role not in required_roles:
            logger.warning(f"Access denied for user {current_user.email}. Role '{current_user.role}' does not have required permissions: {required_roles}")
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


@router.get("/users/me", response_model=AuthUser, dependencies=[Depends(require_viewer)])
async def read_users_me(current_user: AuthUser = Depends(get_current_user)):
    """
    A protected endpoint that returns the current authenticated user's details, including their role.
    """
    return current_user
