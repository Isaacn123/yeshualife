from .base import *
import os

# Override via .env: PROD_DEBUG=False or PROD_DEBUG=True
DEBUG = os.environ.get("PROD_DEBUG", "False").lower() in ("true", "1", "yes")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-9@865u5i22(b6n03#k396q%a84pfbnqsj^*+ua9qp-l7k3#5-!"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

try:
    from .local import *
except ImportError:
    pass
