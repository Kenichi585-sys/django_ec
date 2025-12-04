from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASE_URL = os.environ.get('DATABASE_URL')

DATABASES = {
    "default": env.db(),
}


