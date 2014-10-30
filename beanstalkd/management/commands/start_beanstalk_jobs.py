import logging
from optparse import make_option
from time import sleep
from beanstalkd import settings, tubes, get_proxy, exceptions
from beanstalkc import SocketError
from django.core.management import BaseCommand
from django.db import DatabaseError
from django.utils import importlib
import cPickle as pickle
import uuid

STOP_FILE = '/var/beanstalkd/.stop_workers'

logger = logging.getLogger('beanstalkd.worker')
logger.setLevel(settings.LOGGING_LEVEL)

do_stop = False

STATUS_WAITING = 0
STATUS_PROCESSING = 1
status = STATUS_WAITING


class Worker(object):
    def initialize_connection(self):
        try:
            self.connection = get_proxy()
        except SocketError:
            return False

        if not self.connection:
            return

        for tube in self.tubes:
            self.connection.watch(tube)

        return self.connection

    def __init__(self, overrive_tubes=None):
        super(Worker, self).__init__()
        self.tubes = overrive_tubes or tubes.as_list()
        self.connection = None
        self.id = unicode(uuid.uuid4())
        logger.info(u'Spawning worker {}'.format(self.id))

    @staticmethod
    def __get_job(job_path):
        path_parts = job_path.split(u'.')
        path, job_var = u'.'.join(path_parts[0:-1]), path_parts[-1]
        module = importlib.import_module(path)
        return getattr(module, job_var)

    def loop(self):
        while not do_stop:
            try:
                self.perform_job()
            except SocketError:
                logger.error(u'Lost connection with beanstalkd')
                sleep(10)

    def perform_job(self):
        global status

        status = STATUS_WAITING

        if not self.initialize_connection():
            return

        job = self.connection.reserve()
        status = STATUS_PROCESSING

        conf = pickle.loads(job.body)

        tube = conf['name']
        job_func = self.__get_job(tube)
        job_uuid = str(uuid.uuid4())
        job_args = conf['params']['args']
        job_kwargs = conf['params']['kwargs']

        tube_conf = tubes.get_tube_conf(job_func)

        is_job_kwarg_required = tube_conf.get('is_job_kwarg_required', False)

        if is_job_kwarg_required:
            job_kwargs['job'] = job

        message_tpl = u'Worker {}. Job {}. {} job {} ' \
                      u'with args {} and kwargs {}. '
        info_message = message_tpl.format(
            self.id, job_uuid, u'Started', tube, job_args, job_kwargs,
        )
        finish_message = message_tpl.format(
            self.id, job_uuid, u'Finished', tube, job_args, job_kwargs,
        )
        fail_message = message_tpl.format(
            self.id, job_uuid, u'Failed', tube, job_args, job_kwargs,
        )

        logger.info(info_message)

        job_func.deferred = False
        try:
            job_func(*job_args, **job_kwargs)
            self.complete_job(finish_message, job)
        except DatabaseError as e:
            # renew django database connection
            from django.db import connection
            connection.close()
            self.fail_job(
                tube_conf, job, u'{} {}'.format(fail_message, e.message)
            )
        except exceptions.SilentFailException:
            self.fail_job(
                tube_conf, job,
                None
            )
        except Exception as e:
            import sys
            import traceback

            exc_type, exc_value, exc_traceback = sys.exc_info()

            exception_message = u'\n\n{} {} \n {}'.format(
                exc_type, exc_value,
                traceback.format_exc(exc_traceback)
            )
            self.fail_job(
                tube_conf, job,
                fail_message + e.message + exception_message
            )
        finally:
            job_func.deferred = True

    def complete_job(self, finish_message, job):
        self.connection.finish(job)
        logger.info(finish_message)

    def fail_job(self, conf, job, fail_message):
        if fail_message:
            logger.error(fail_message)

        is_critical = conf.get('critical', True)
        retry_on_fail = conf.get('retry', False)

        if retry_on_fail:
            self.connection.retry(job)
            return

        if is_critical:
            self.connection.bury(job)
            return

        self.connection.finish(job)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--tube', dest='tube', type=str, default=None),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.children = []

    def handle(self, *args, **options):
        tube = options.pop('tube')
        if tube:
            w = Worker(overrive_tubes=[tube])
        else:
            w = Worker()
        w.loop()
