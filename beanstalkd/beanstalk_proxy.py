import logging
import cPickle as pickle

import beanstalkc
from django.db import DatabaseError

import yaml

from . import settings, models, tubes


logger = logging.getLogger('beanstalkd')


class BeanstalkProxy(object):
    def __init__(self, connection=None):
        super(BeanstalkProxy, self).__init__()
        self._connection = connection

    @property
    def connection(self):
        if self._connection:
            return self._connection

        try:
            self._connection = beanstalkc.Connection(
                host=settings.HOST,
                port=settings.PORT,
                parse_yaml=settings.PARSE_YAML
            )
            self.connection.ignore('default')
        except beanstalkc.SocketError:
            logger.error('Beanstalk unavailable')

        return self._connection

    def __get_db_job_by_beanstalk_job(self, job):
        db_job = None
        conf = pickle.loads(job.body)
        db_job_id = conf.get('db_job_id')

        if db_job_id:
            try:
                db_job = models.Job.objects.get(
                    id=db_job_id
                )
            except models.Job.DoesNotExist:
                db_job = None

        if not db_job:
            db_job = models.Job.objects.filter(
                beanstalk_id=job.jid
            ).latest('created_at')

        return db_job

    def reserve(self, connection=None):
        if not connection:
            connection = self.connection

        job = connection.reserve()

        if not job:
            return

        db_job = self.__get_db_job_by_beanstalk_job(job)
        if db_job:
            db_job.state = models.Job.PROCESSING
            db_job.save(force_update=True)
        else:
            msg = 'Set processing state faster than job was created: {}'
            logger.info(msg.format(job.jid))
        return job

    def __put(self, tube_name, message, delay=0, connection=None):
        connection.use(tube_name)
        job = None
        try:
            if delay:
                state = models.Job.DELAYED
            else:
                state = models.Job.IN_QUEUE

            job = models.Job.objects.create(
                beanstalk_id=0,
                tube_name=tube_name,
                instance_ip=settings.HOST,
                instance_port=settings.PORT,
                state=state
            )
            message['db_job_id'] = job.id
        except DatabaseError:
            # We intentionally swallow this error, because we dont want to
            # cancel job due to database errors
            msg = 'Unable to create database record for new job {message}'
            logger.error(msg.format(
                message=message
            ))

        try:
            job_id = connection.put(
                pickle.dumps(message),
                delay=delay,
                ttr=settings.DEFAULT_TIME_TO_RUN
            )
        except Exception:
            if job:
                job.delete()
            raise

        if job:
            try:
                job.beanstalk_id = int(job_id)
                job.message = message
                job.save(update_fields=(
                    'beanstalk_id',
                    'message',
                    'digest'
                ))
            except DatabaseError as e:
                # We intentionally swallow this error, because we dont want to
                # cancel job due to database errors
                pass

    def put(self, tube_name, message, delay=0, connection=None):
        if not connection:
            connection = self.connection

        connection.use(tube_name)

        if settings.USE_TRANSACTION_SIGNALS:
            import django_transaction_signals
            django_transaction_signals.defer(
                self.__put,
                tube_name, message, delay=delay, connection=connection
            )
        else:
            self.__put(tube_name, message, delay=delay, connection=connection)

    def bury(self, job_or_job_id, connection=None):
        if not connection:
            connection = self.connection
        job = self.get_job(connection, job_or_job_id)

        if not job:
            return

        try:
            connection.bury(job.jid)
        except beanstalkc.CommandFailed as e:
            if e.message != 'NOT_FOUND':
                raise

        try:
            db_job = self.__get_db_job_by_beanstalk_job(job)
            if db_job:
                db_job.state = models.Job.BURIED
                db_job.save(force_update=True)
            else:
                msg = 'Bury job faster than job was created: {}'
                logger.info(msg.format(job.jid))
        except DatabaseError as e:
            # We intentionally swallow this error, because we dont want to
            # cancel job due to database errors
            msg = 'Unable to bury job for id: {} {}'
            logger.error(msg.format(job.jid, e))

    def get_job(self, connection, job_or_job_id):
        job = job_or_job_id
        if isinstance(job_or_job_id, int):
            job = connection.peek(job_or_job_id)
        return job

    def delete(self, job_or_job_id, state, connection=None):
        if not connection:
            connection = self.connection
        job = self.get_job(connection, job_or_job_id)

        if not job:
            return

        try:
            job.delete()
        except beanstalkc.CommandFailed as e:
            if e.message != 'NOT_FOUND':
                raise

        try:
            db_job = self.__get_db_job_by_beanstalk_job(job)
            if db_job:
                db_job.state = state
                db_job.save(force_update=True)
            else:
                msg = 'Finished job faster than job was created: {}'
                logger.info(msg.format(job.jid))
        except DatabaseError:
            # We intentionally swallow this error, because we dont want to
            # cancel job due to database errors
            msg = 'Unable to delete job for id: {}'
            logger.error(msg.format(job.jid))

    def finish(self, job_or_job_id, connection=None):
        self.delete(
            job_or_job_id,
            state=models.Job.COMPLETE,
            connection=connection
        )

    def retry(self, job_or_job_id, delay=None, connection=None):
        if not connection:
            connection = self.connection

        job = self.get_job(connection, job_or_job_id)

        self.delete(
            job_or_job_id,
            state=models.Job.FAILED,
            connection=connection
        )

        message = pickle.loads(job.body)
        tube_settings = tubes.get_tube_conf(message['name'])
        default_delay = settings.DEFAULT_RETRY_DELAY
        self.put(
            message['name'],
            message,
            tube_settings.get('retry_delay', delay or default_delay)
        )

    def kick(self, job_or_job_id, connection=None):
        if not connection:
            connection = self.connection

        job = self.get_job(connection, job_or_job_id)
        connection.kick_job(job.jid)

    def update_tube_stats(self, tube_name, connection=None):
        if not connection:
            connection = self.connection

        yaml_stats = connection.stats_tube(tube_name)
        stats = yaml.load(yaml_stats)

        models.Tube.objects.filter(
            name=tube_name
        ).update(
            buried=int(stats.get('current-jobs-buried', 0)),
            delayed=int(stats.get('current-jobs-delayed', 0)),
            ready=int(stats.get('current-jobs-ready', 0)),
            reserved=int(stats.get('current-jobs-reserved', 0)),
            urgent=int(stats.get('current-jobs-urgent', 0)),
        )

    def watch(self, tube_name):
        self.connection.watch(tube_name)
