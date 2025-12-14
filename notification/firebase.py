import os
import threading
from django.conf import settings
from firebase_admin import credentials, initialize_app, get_app
from settings.models import FirebaseSettings
from django.core.files.storage import default_storage

_init_lock = threading.Lock()
_initialized = False

def init_firebase():
    global _initialized
    if _initialized:
        return get_app()
    with _init_lock:
        if _initialized:
            return get_app()
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
            raise RuntimeError('Firebase config file not found on disk.')

        cred = credentials.Certificate(file_path)
        initialize_app(cred)
        _initialized = True
        return get_app()