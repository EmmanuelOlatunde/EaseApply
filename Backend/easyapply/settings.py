from pathlib import Path
import os
from datetime import timedelta
from decouple import config
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ Load the .env file FIRST
load_dotenv(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-@-6)las_@%doa9=r5g2&wo!@u%mvy)2@yl_+ftc5w&_$fa$fl%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["easeapply.onrender.com"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    "corsheaders",

    # Local apps
    'users',
    'resumes',
    'jobs',
    'analysis',
    'common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'easyapply.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


CORS_ALLOW_ALL_ORIGINS = True

WSGI_APPLICATION = 'easyapply.wsgi.application'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",   # React dev server
    "http://127.0.0.1:8000",  # Swagger UI
]

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'easeapply',
        'USER': 'easeadmin',
        'PASSWORD': '@Mohbohlahji55!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


OPENROUTER_API_KEY_KIMI = os.getenv("OPENROUTER_API_KEY_KIMI")

if not OPENROUTER_API_KEY_KIMI:
    raise ValueError("OPENROUTER_API_KEY_KIMI environment variable is required")

API_KEYS = {
    "kimi": os.getenv("OPENROUTER_API_KEY_KIMI"),
    "qwen": os.getenv("OPENROUTER_API_KEY_QWEN"),
    "deepseek": os.getenv("OPENROUTER_API_KEY_DEEPSEEK"),
}

if not API_KEYS:
    raise ValueError("API_KEYS environment variable is required")

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
       
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '5/minute',   # or whatever limit you want
        'anon': '10/minute',
    },
    
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',  
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# # Djoser Configuration
# DJOSER = {
#     'LOGIN_FIELD': 'email',
#     'USER_CREATE_PASSWORD_RETYPE': True,
#     'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
#     'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
#     'SEND_CONFIRMATION_EMAIL': True,
#     'SET_USERNAME_RETYPE': True,
#     'SET_PASSWORD_RETYPE': True,
#     'PASSWORD_RESET_CONFIRM_URL': 'password/reset/confirm/{uid}/{token}',
#     'USERNAME_RESET_CONFIRM_URL': 'username/reset/confirm/{uid}/{token}',
#     'ACTIVATION_URL': 'activate/{uid}/{token}',
#     'SEND_ACTIVATION_EMAIL': True,
#     'SERIALIZERS': {
#         'user_create': 'users.serializers.UserRegistrationSerializer',
#         'user': 'users.serializers.UserSerializer',
#         'current_user': 'users.serializers.UserSerializer',
#         'user_delete': 'djoser.serializers.UserDeleteSerializer',
#     },
#     'PERMISSIONS': {
#         'user': ['rest_framework.permissions.IsAuthenticated'],
#         'user_list': ['rest_framework.permissions.IsAdminUser'],
#     }
# }

# Email Configuration (for password reset)

EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "olemmanuel2061@gmail.com")


# Media Files Configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644


# # CORS Configuration (if using frontend)
# CORS_ALLOWED_ORIGINS = [
#     "http://127.0.0.1:8000",
#     "http://localhost:8000",
  
# ]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'users': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

FRONTEND_URL = "http://localhost:5173"

# # Cache Configuration (optional but recommended)
# CACHES = {
#    'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "unique-dev",
#     }
# }
# Upstash Redis Configuration
UPSTASH_REDIS_URL = config('UPSTASH_REDIS_URL')
UPSTASH_REDIS_REST_URL = config('UPSTASH_REDIS_REST_URL')
UPSTASH_REDIS_REST_TOKEN = config('UPSTASH_REDIS_REST_TOKEN')
UPSTASH_REDIS_READONLY_TOKEN = config('UPSTASH_REDIS_READONLY_TOKEN', default='')

# Cache configuration using Upstash Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': UPSTASH_REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {},
                'health_check_interval': 30,
            }
        },
        'KEY_PREFIX': 'myapp',  # Replace with your app prefix
        'TIMEOUT': 300,  # Default timeout of 5 minutes
    }
}

# Session configuration - Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False

SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF Configuration
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT format: Bearer <token>'
        }
    },
    'USE_SESSION_AUTH': False,
}


# Redis Service Configuration
REDIS_SERVICE_CONFIG = {
    'DEFAULT_TIMEOUT': 300,  # 5 minutes
    'USER_CACHE_TIMEOUT': 3600,  # 1 hour
    'SESSION_TIMEOUT': 86400,  # 24 hours
    'API_RATE_LIMIT_TIMEOUT': 3600,  # 1 hour
}

# Get the base URL
base_url = config('CELERY_BROKER_URL')

# Add SSL parameter if it's a rediss:// URL
if base_url.startswith('rediss://'):
    if '?' in base_url:
        CELERY_BROKER_URL = base_url + '&ssl_cert_reqs=none'
    else:
        CELERY_BROKER_URL = base_url + '?ssl_cert_reqs=none'
else:
    CELERY_BROKER_URL = base_url

CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# CELERY_BROKER_URL = config('CELERY_BROKER_URL')
# CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# CELERY_BROKER_USE_SSL = {
#     'ssl_cert_reqs': ssl.CERT_NONE
# }
# CELERY_RESULT_BACKEND_USE_SSL = CELERY_BROKER_USE_SSL

# Optional reliability settings
CELERY_TASK_ALWAYS_EAGER = False
CELERY_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
