# src/backend/services/firebase_admin.py

import firebase_admin
from firebase_admin import credentials
from core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

def initialize_firebase_admin():
    """
    Initializes the Firebase Admin SDK using the service account key file.
    """
    # Check if the app is already initialized to prevent errors.
    if not firebase_admin._apps:
        try:
            # Construct the path to the service account key.
            # Assumes the script is run from the `src/backend` directory.
            service_account_key_path = "core/serviceAccountKey.json"

            if not os.path.exists(service_account_key_path):
                logger.error(f"Service account key not found at '{service_account_key_path}'.")
                logger.error("Please ensure 'serviceAccountKey.json' is in the 'src/backend/core' directory.")
                return

            cred = credentials.Certificate(service_account_key_path)
            
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID,
            })
            logger.info("Firebase Admin SDK initialized successfully using service account file.")
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin SDK: {e}")
    else:
        logger.info("Firebase Admin SDK already initialized.")

