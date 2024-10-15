import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(".env")

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "drf_spectacular",
    "Main",
    "Users"
]

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = True if os.environ["DEBUG_MODE"].lower() == "true" else False

ALLOWED_HOSTS = ["*", "0.0.0.0"]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'polikek_rf.urls'

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["Templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'polikek_rf.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ["DB_NAME"],
        'USER': os.environ["DB_USERNAME"],
        'PASSWORD': os.environ["DB_PASSWORD"],
        'HOST': os.environ["DB_HOST"],
        'PORT': os.environ["DB_PORT"],
    }
}

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = ""
AUTHENTICATION_BACKENDS = []
REST_FRAMEWORK = {
    'COMPONENT_SPLIT_REQUEST': True,
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
        'rest_framework.parsers.JSONParser',
    ]
}
APPEND_SLASH = True
CSP_SCRIPT_SRC = ("'self'", 'ajax.googleapis.com', "'unsafe-inline'")
SMARTCAPTCHA_ENABLED = True if os.environ.get("SMARTCAPTCHA_ENABLED").lower() == "true" else False
SMARTCAPTCHA_SERVER_KEY=os.environ.get("SMARTCAPTCHA_SERVER_KEY")

TEMPLATES_PATH = os.path.join(BASE_DIR, 'Templates')
