import functools

import logging

from .tubes import get_tube_conf
from .models import Job

logger = logging.getLogger('beanstalkd')

DEFAULT_TUBE = 'default'


def job(func):
    def synchronous_call(args, kwargs):
        return func(*args, **kwargs)

    def asynchronous_call(proxy, job_conf, args, kwargs):
        tube_name = job_conf['name']
        logger.info(u'Sending job. {}'.format(tube_name))

        is_unique = job_conf.get('unique', False)

        message = {
            'name': tube_name,
            'params': {
                'args': args,
                'kwargs': kwargs
            }
        }
        if is_unique:
            digest = Job.get_message_digest(message)
            if Job.objects.in_queue().filter(digest=digest).exists():
                return

        proxy.put(tube_name, message)
        return

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from . import settings

        if settings.DISABLE:
            return synchronous_call(args, kwargs)

        from . import get_proxy
        beanstalk_proxy = get_proxy()

        job_conf = get_tube_conf(func)
        tube_name = job_conf['name']

        is_deferred_default = job_conf.get('deferred', False)
        is_deferred = getattr(wrapper, 'deferred', is_deferred_default)

        if not is_deferred:
            return synchronous_call(args, kwargs)

        is_critical = job_conf.get('critical', False)

        if beanstalk_proxy.connection:
            return asynchronous_call(
                beanstalk_proxy,
                job_conf,
                args,
                kwargs
            )

        if is_critical:
            logger.info(
                u'Fallback to synchronous workflow {}'.format(tube_name)
            )
            return synchronous_call(args, kwargs)

        logger.info(u'Ignoring job. No connection. {}'.format(tube_name))

    return wrapper
