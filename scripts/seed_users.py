# src/backend/scripts/seed_users.py

import sys
import os
import asyncio
from firebase_admin import auth, firestore

# Add the project root to the Python path to allow importing from 'core' and 'services'
# This assumes the script is run from the `src/backend` directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.firebase_admin import initialize_firebase_admin

# --- User Definitions ---
# IMPORTANT: Use strong, unique passwords in a real production environment.
# This is for testing purposes only.
USERS_TO_CREATE = [
    {
        "email": "admin@netverse.io",
        "password": "Password123",
        "role": "admin",
        "display_name": "Admin User"
    },
    {
        "email": "analyst@netverse.io",
        "password": "Password123",
        "role": "analyst",
        "display_name": "Analyst User"
    },
    {
        "email": "viewer@netverse.io",
        "password": "Password123",
        "role": "viewer",
        "display_name": "Viewer User"
    }
]

async def seed_users():
    """
    Creates predefined users in Firebase Authentication with custom roles.
    If a user already exists, it updates their role and display name.
    """
    print("🔥 Initializing Firebase Admin SDK...")
    initialize_firebase_admin()
    print("✅ Firebase Admin SDK initialized.")
    print("-" * 30)

    db = firestore.client()
    for user_def in USERS_TO_CREATE:
        email = user_def["email"]
        password = user_def["password"]
        role = user_def["role"]
        display_name = user_def["display_name"]

        try:
            # Check if user exists
            user = auth.get_user_by_email(email)
            print(f"🔄 User {email} already exists. Updating role and display name...")
            # Update user's display name
            auth.update_user(user.uid, display_name=display_name)
            # Update custom claims (role)
            auth.set_custom_user_claims(user.uid, {'role': role})
            print(f"✅ Successfully updated {email} to role '{role}'.")
            print(f"ℹ️  [INFO] Credentials for {email}: password='{password}' (for backend seeding only)")
            uid = user.uid
        except auth.UserNotFoundError:
            # User does not exist, create them
            print(f"✨ Creating new user: {email} with role '{role}'...")
            try:
                new_user = auth.create_user(
                    email=email,
                    password=password,
                    display_name=display_name,
                    email_verified=True # Set to true for testing convenience
                )
                # Set the custom claim for the new user
                auth.set_custom_user_claims(new_user.uid, {'role': role})
                print(f"✅ Successfully created new user {email} (UID: {new_user.uid}) with role '{role}'.")
                print(f"ℹ️  [INFO] Credentials for {email}: password='{password}' (for backend seeding only)")
                uid = new_user.uid
            except Exception as e:
                print(f"❌ Error creating user {email}: {e}")
                continue
        except Exception as e:
            print(f"❌ An unexpected error occurred for user {email}: {e}")
            continue

        # Ensure user exists in Firestore database
        try:
            user_doc_ref = db.collection("users").document(uid)
            user_doc_ref.set({
                "uid": uid,
                "email": email,
                "role": role,
                "display_name": display_name,
            }, merge=True)
            print(f"✅ Firestore user document ensured for {email} (uid: {uid})")
        except Exception as e:
            print(f"⚠️  Firestore error for {email}: {e}")
        print("-" * 30)
    
    print("🚀 User seeding process complete!")


if __name__ == "__main__":
    # To run this script:
    # 1. Make sure you are in the `src/backend` directory.
    # 2. Activate the virtual environment: `source venv/bin/activate`
    # 3. Run the script: `python scripts/seed_users.py`
    asyncio.run(seed_users())
