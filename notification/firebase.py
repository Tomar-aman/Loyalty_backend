import os
import threading
from django.conf import settings
from firebase_admin import credentials, initialize_app, get_app, exceptions
from settings.models import FirebaseSettings
from django.core.files.storage import default_storage

_init_lock = threading.Lock()
_initialized = False

def init_firebase():
    """
    Initialize Firebase Admin SDK lazily on first use.
    This is thread-safe and database-query happens only when called.
    """
    global _initialized
    if _initialized:
        try:
            return get_app()
        except ValueError:
            # App was deleted or not initialized, reset flag
            _initialized = False
    
    with _init_lock:
        if _initialized:
            try:
                return get_app()
            except ValueError:
                _initialized = False
        
        # Query database only when init_firebase is actually called
        fb = FirebaseSettings.objects.order_by('-updated_at').first()
        if not fb or not fb.config_file:
            raise RuntimeError('Firebase config file is not set.')
        
        # Ensure we have a local file path
        file_path = fb.config_file.path
        if not os.path.exists(file_path):
            # Try to get a local copy from storage
            if default_storage.exists(fb.config_file.name):
                file_path = default_storage.path(fb.config_file.name)
        
        if not os.path.exists(file_path):
            raise RuntimeError(f'Firebase config file not found at: {file_path}')

        cred = credentials.Certificate(file_path)
        initialize_app(cred)
        _initialized = True
        return get_app()


def reset_firebase():
    """Reset Firebase initialization state (useful after config update)."""
    global _initialized
    with _init_lock:
        _initialized = False
        try:
            import firebase_admin
            firebase_admin.delete_app(get_app())
        except ValueError:
            pass