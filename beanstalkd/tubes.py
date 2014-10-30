import os
import yaml
import logging

logger = logging.getLogger('beanstalkd')


__tube_registry = None


def __get_tube_registry(force_reload=False):
    global __tube_registry
    if force_reload:
        __tube_registry = None

    if not __tube_registry or force_reload:
        from beanstalkd import settings

        load_tubes(settings.JOBS_CONF_NAME)

        for app in settings.INSTALLED_APPS:
            path = os.path.join(settings.BASE_DIR, app)
            load_tubes('{}/{}'.format(path, settings.JOBS_CONF_NAME))

        for path in settings.JOBS_CONF_PATHS:
            if not path.startswith('/'):
                path = os.path.join(settings.BASE_DIR, path)
                load_tubes(path)
            else:
                load_tubes(path)

    return __tube_registry


def as_list(force_reload=False):
    tube_registry = __get_tube_registry(force_reload=force_reload)
    result = []
    for job_path, job_settings in tube_registry.iteritems():
        if not job_settings.get('deferred', False):
            continue

        result.append(job_path)
    return result


def load_tubes(*conf_files):
    global __tube_registry

    for path in conf_files:
        try:
            with open(path, 'r') as conf:
                job_conf = yaml.load(conf) or {}
                if not __tube_registry:
                    __tube_registry = job_conf or {}
                else:
                    __tube_registry.update(job_conf)
        except IOError:
            continue

    if not __tube_registry:
        file_paths = u'\n\t'.join(conf_files)
        logger.warn(
            u'Beanstalk Job file not found. Locations were: {}'.format(
                file_paths
            )
        )
        __tube_registry = {}


def get_tube_conf(func_or_path):
    job_registry = __get_tube_registry()

    if isinstance(func_or_path, basestring):
        name = func_or_path
    else:
        func = func_or_path
        name = u'{}.{}'.format(func.__module__, func.__name__)

    conf = job_registry.get(name, {})
    conf['name'] = name
    return conf


def reset_registry():
    global __tube_registry
    __tube_registry = None