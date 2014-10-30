#!/usr/bin/env python

from os.path import dirname, join
import sys
from optparse import OptionParser
import warnings
import django

def parse_args():
    parser = OptionParser()
    parser.add_option('--use-tz', dest='USE_TZ', action='store_true')
    return parser.parse_args()


def configure_settings(options):
    import os
    from django.conf import settings

    # If DJANGO_SETTINGS_MODULE envvar exists the settings will be
    # configured by it. Otherwise it will use the parameters bellow.
    if not settings.configured:
        installed_apps = [
            'django.contrib.contenttypes',
            'beanstalkd',
            'tests',
        ]
        if django.VERSION < (1, 7):
            installed_apps.append(
                'south',
            )

        params = dict(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            PROJECT_ROOT=os.path.abspath(
                os.path.dirname(__file__)
            ),
            INSTALLED_APPS=installed_apps,
            MIDDLEWARE_CLASSES=(

            ),
            ADMINS = (
                'admin@zzz.com',
            ),
            EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend',
            EMAIL_FILE_PATH = '/tmp/extrota-messages',
            LOGGING = {
                'version': 1,
                'disable_existing_loggers': True,
                'handlers': {
                    'mail_admins': {
                        'level': 'ERROR',
                        'class': 'django.utils.log.AdminEmailHandler',
                        'include_html': True,
                        'filters': [],
                    },
                },
                'loggers': {
                    'beanstalkd': {
                        'handlers': ['mail_admins', ],
                        'level': 'ERROR',
                        'propagate': False,
                    },
                },
            },
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                    'LOCATION': 'unique-snowflake'
                }
            },
            SITE_ID=1,
            TEST_RUNNER='django.test.runner.DiscoverRunner',
            TEST_ROOT=join(dirname(__file__), 'tests'),
        )
        settings.configure(**params)

    return settings


def get_runner(settings):
    '''
    Asks Django for the TestRunner defined in settings or the default one.
    '''
    from django.test.utils import get_runner

    TestRunner = get_runner(settings)

    if django.VERSION >= (1, 7):
        # I suspect this will not be necessary in next release after 1.7.0a1:
        #  See https://code.djangoproject.com/ticket/21831
        setattr(settings, 'INSTALLED_APPS',
                ['django.contrib.auth']
                + list(getattr(settings, 'INSTALLED_APPS')))
    return TestRunner(verbosity=1, interactive=True, failfast=False)


def runtests(options=None, labels=None):
    settings = configure_settings(options)
    runner = get_runner(settings)

    if django.VERSION >= (1, 7):
        django.setup()

    if django.VERSION <= (1, 7):
        from south.management import commands
        commands.patch_for_test_db_setup()

    sys.exit(runner.run_tests(labels))

if __name__ == '__main__':
    options, labels = parse_args()
    runtests(options, labels)