"""
Django settings for gunahasite project.

Generated by 'django-admin startproject' using Django 2.2.12.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import logging.config
import os
from pathlib import Path
from typing import List

from environs import Env

# Load env from .env file
env = Env()
env.read_env()

# Build paths inside the project like this: BASE_PATH / 'path' / 'to' / 'file'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = Path(BASE_DIR).resolve()

INVALID_SECRET_KEY = object()


########################### ENVIRONMENT VARIABLES ############################

# General settings

# Django would like you to refer to this document before deploy:
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# Enable Django debug: leave this off in production
DEBUG = env.bool("DEBUG", False)

# The encryption key! Please keep this secret!
SECRET_KEY = env("SECRET_KEY", INVALID_SECRET_KEY)

# How noisy should the console logs be.
LOG_LEVEL = env.log_level("LOG_LEVEL", "WARN")

# Which domains can access this site?
ALLOWED_HOSTS: List[str] = env.list("ALLOWED_HOSTS", ["localhost"])

############################## ENV: DIRECTORIES ##############################

# Where persistent data will be placed
DATA_DIR = env.path("DATA_DIR", os.fspath(BASE_PATH / "run"))

############################### ENV: DATABASES ###############################

with env.prefixed("DATABASE_"):
    DATABASE_ENGINE = env("ENGINE", "django.db.backends.sqlite3")
    DATABASE_NAME = env("NAME", os.fspath(DATA_DIR / "db.sqlite3"))
    DATABASE_LOG_LEVEL = env.log_level("LOG_LEVEL", "WARN")

############################# ENV: STATIC FILES ##############################

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
with env.prefixed("STATIC_"):
    # Where collectstatic will dump files:
    STATIC_ROOT = env("ROOT", None)
    # The URL prefix for all static files. MUST end with a slash!
    STATIC_URL = env("URL", "/static/")


################################# VALIDATION #################################

if SECRET_KEY is INVALID_SECRET_KEY:
    print(
        "\033[31m" "Warning: no SECRET_KEY set!",
        " * Using an invalid key to work in development environment",
        " * only allow connections from localhost (no public access)" "\033[m",
        sep="\n",
    )
    SECRET_KEY = "<invalid>"
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


##################### REQUIRED SETTINGS FOR APPLICATIONS #####################

# Applications required for this site:

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "haystack",
    # Local
    "apps.gunaha.apps.GunahaConfig",
    "apps.morphodict.apps.MorphoDictConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gunahasite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gunahasite.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {"default": {"ENGINE": DATABASE_ENGINE, "NAME": DATABASE_NAME,}}

############################ Full-text search with Haystack ############################

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": os.fspath(DATA_DIR / "whoosh_index"),
    },
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-ca"

# Alberta time zone.
# (developers are in Edmonton)
# (community is in Tsuut'ina Nation, near Calgary)
TIME_ZONE = "America/Edmonton"

USE_I18N = True

USE_L10N = True

USE_TZ = True

################################## Logging ###################################

# Disable default Django logging:
LOGGING_CONFIG = None

# Opionionated logger: the only setting is log level.
# View these in docker with:
#
#   docker logs
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s %(levelname)-8s %(process)d [%(name)s:%(lineno)s]: %(message)s"
            },
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "console"},
        },
        "loggers": {
            "apps": {"handlers": ["console"], "level": LOG_LEVEL,},
            "django.db": {"handlers": ["console"], "level": DATABASE_LOG_LEVEL,},
        },
    }
)
