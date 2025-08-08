# src/backend/services/firebase_admin.py

import firebase_admin
from firebase_admin import credentials
from core.config import settings
import os
import logging
import json

logger = logging.getLogger(__name__)

def initialize_firebase_admin():
    """
    Initializes the Firebase Admin SDK.
    It first tries to load credentials from an environment variable (for cloud deployments)
    and falls back to a local file (for local development).
    """
    # Check if the app is already initialized to prevent errors.
    if firebase_admin._apps:
        logger.info("Firebase Admin SDK already initialized.")
        return

    try:
        # --- Method 1: Environment Variable (for production/cloud) ---
        service_account_json_str = settings.FIREBASE_SERVICE_ACCOUNT_JSON
        if service_account_json_str:
            try:
                service_account_info = json.loads(service_account_json_str)
                cred = credentials.Certificate(service_account_info)
                firebase_admin.initialize_app(cred, {'projectId': settings.FIREBASE_PROJECT_ID})
                logger.info("Firebase Admin SDK initialized successfully from environment variable.")
                return
            except json.JSONDecodeError:
                logger.error("Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON. Ensure it's valid JSON.")
            except Exception as e:
                logger.error(f"Error initializing Firebase from env var: {e}")

        # --- Method 2: Local File (for local development) ---
        service_account_key_path = "core/serviceAccountKey.json"
        if os.path.exists(service_account_key_path):
            cred = credentials.Certificate(service_account_key_path)
            firebase_admin.initialize_app(cred, {'projectId': settings.FIREBASE_PROJECT_ID})
            logger.info("Firebase Admin SDK initialized successfully using service account file.")
            return

        # If neither method works
        logger.error("Failed to initialize Firebase Admin SDK. No valid credentials found.")
        logger.error("Provide FIREBASE_SERVICE_ACCOUNT_JSON env var or place serviceAccountKey.json in core/.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during Firebase initialization: {e}")
