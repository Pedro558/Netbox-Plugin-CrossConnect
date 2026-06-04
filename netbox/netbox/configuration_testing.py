###################################################################
#  This file serves as a base configuration for testing purposes  #
#  only. It is not intended for production use.                   #
###################################################################

from .configuration import DATABASES as LOCAL_DATABASES

ALLOWED_HOSTS = ['*']

DEVELOPER = True

DATABASES = {
    'default': {
        'NAME': 'netbox',
        'USER': 'netbox',
        'PASSWORD': LOCAL_DATABASES.get('default', {}).get('PASSWORD', 'netbox'),
        'HOST': 'localhost',
        'PORT': '',
        'CONN_MAX_AGE': 300,
    }
}

PLUGINS = [
    'netbox.tests.dummy_plugin',
    'netbox_cross_connects',
]

REDIS = {
    'tasks': {
        'HOST': 'localhost',
        'PORT': 6379,
        'USERNAME': '',
        'PASSWORD': '',
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'HOST': 'localhost',
        'PORT': 6379,
        'USERNAME': '',
        'PASSWORD': '',
        'DATABASE': 1,
        'SSL': False,
    }
}

SECRET_KEY = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

DEFAULT_PERMISSIONS = {}

ALLOW_TOKEN_RETRIEVAL = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True
}
