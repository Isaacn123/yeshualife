from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-9@865u5i22(b6n03#k396q%a84pfbnqsj^*+ua9qp-l7k3#5-!"

# SECURITY WARNING: define the correct hosts in production!
# ALLOWED_HOSTS = ["*"]
ALLOWED_HOSTS = ['yeshualifeug.com', 'www.yeshualifeug.com', '167.99.117.231', '127.0.0.1']
# ALLOWED_HOSTS = ['http://yeshualifeug.com', 'http://167.99.117.231']

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    from .local import *
except ImportError:
    pass
