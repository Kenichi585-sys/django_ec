from .base import *
import dj_database_url
import os

DEBUG = False

ALLOWED_HOSTS = [os.environ.get('HOST_NAME', 'hc-ec-site.herokuapp.com')]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True, conn_health_checks=True)
}
DEBUG_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
print(f"DEBUG: CLOUDINARY_CLOUD_NAME is: {DEBUG_CLOUD_NAME}")
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET
}
