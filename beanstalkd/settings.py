import datetime
from django.conf import settings

BASE_DIR = getattr(settings, 'BASE_DIR', None)
if not BASE_DIR:
    BASE_DIR = getattr(settings, 'PROJECT_ROOT', None)

INSTALLED_APPS = getattr(settings, 'INSTALLED_APPS', [])

HOST = getattr(settings, 'BEANSTALKD_HOST', '127.0.0.1')
PORT = getattr(settings, 'BEANSTALKD_PORT', 11301)
PARSE_YAML = getattr(settings, 'BEANSTALKD_PARSE_YAML', False)

JOBS_CONF_NAME = getattr(settings, 'BEANSTALKD_JOBS_CONF_NAME', 'jobs.yaml')

JOBS_CONF_PATHS = getattr(settings, 'JOBS_CONF_PATHS', ())

LOGGING_LEVEL = getattr(settings, 'BEANSTALKD_LOGGING_LEVEL', 'DEBUG')

DISABLE = getattr(settings, 'BEANSTALKD_DISABLE', False)

OLD_JOB_AGE = getattr(
    settings,
    'BEANSTALKD_OLD_JOB_TIMEDELTA',
    datetime.timedelta(days=1)
)

USE_TRANSACTION_SIGNALS = getattr(
    settings,
    'BEANSTALKD_USE_TRANSACTION_SIGNALS',
    True
)

DEFAULT_RETRY_DELAY = getattr(
    settings,
    'BEANSTALKD_DEFAULT_RESTART_DELAY',
    10 * 60
)

DEFAULT_TIME_TO_RUN = getattr(
    settings,
    'BEANSTALKD_DEFAULT_TIME_TO_RUN',
    10 * 60
)
