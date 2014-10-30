import os
import cPickle as pickle

from django.test import TestCase, utils
from django.conf import settings as django_settings
from django.core import mail
import mock

from beanstalkd import models
from beanstalkd.management.commands.start_beanstalk_jobs import Worker
from beanstalkd.tubes import reset_registry


class TestBeanstalkProxy(TestCase):

    def setUp(self):
        super(TestBeanstalkProxy, self).setUp()
        reset_registry()

    def get_beanstalk_response(self, name):
        path = os.path.join(
            django_settings.PROJECT_ROOT,
            'tests/beanstalk_mock/' + name + '.yaml'
        )
        with open(path, 'r') as f:
            return f.read()

    @mock.patch('beanstalkd.settings')
    def test_configuration_file_with_test_jobs(self, settings):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'

        from beanstalkd import tubes

        expected = ['tests.jobs_for_tests.do_something']
        self.assertListEqual(tubes.as_list(True), expected)

    @mock.patch('beanstalkd.settings')
    def test_empty_configuration_file(self, settings):
        settings.JOBS_CONF_NAME = 'tests/test_jobs_empty.yaml'

        from beanstalkd import tubes

        self.assertListEqual(tubes.as_list(True), [])

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.settings')
    def test_update_tube_stat_command(self, settings, connection):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'

        connection.stats_tube = mock.Mock()
        connection.stats_tube.return_value = \
            self.get_beanstalk_response('tube_stats')

        from beanstalkd.management.commands.update_tube_stats import \
            UpdateTubeStatsCommand

        UpdateTubeStatsCommand().handle()

        tubes = models.Tube.objects.all()
        self.assertEqual(tubes.count(), 1)
        self.assertEqual(tubes[0].urgent, 1)
        self.assertEqual(tubes[0].ready, 2)
        self.assertEqual(tubes[0].reserved, 3)
        self.assertEqual(tubes[0].delayed, 4)
        self.assertEqual(tubes[0].buried, 5)

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.settings')
    def test_job_conf(self, settings, connection):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'

        connection.stats_tube = mock.Mock()
        connection.stats_tube.return_value = \
            self.get_beanstalk_response('tube_stats')

        from .jobs_for_tests import do_something

        from beanstalkd import tubes

        job_settings = tubes.get_tube_conf(do_something)

        self.assertEqual(job_settings['name'],
                         u'tests.jobs_for_tests.do_something')
        self.assertEqual(job_settings['critical'], False)
        self.assertEqual(job_settings['deferred'], True)
        self.assertEqual(job_settings['retry'], True)
        self.assertEqual(job_settings['retry_delay'], 300)
        self.assertEqual(job_settings['note'], u'Your momma is a bitch')

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.settings')
    def test_call_deferred_job(self, settings, connection):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'
        settings.DISABLE = False

        from .jobs_for_tests import do_something

        do_something(1, 2, 3, a=1, b=2, c=3)

        self.assertEqual(models.Job.objects.count(), 1)
        job = models.Job.objects.all()[0]

        message = {
            'db_job_id': job.id,
            'name': u'tests.jobs_for_tests.do_something',
            'params': {
                'args': (1, 2, 3),
                'kwargs': {
                    'a': 1,
                    'b': 2,
                    'c': 3,
                }
            }
        }
        connection.put.assert_called_once_with(pickle.dumps(message), delay=0,
                                               ttr=600)
        self.assertEqual(job.tube.name,
                         u'tests.jobs_for_tests.do_something')
        self.assertDictEqual(job.message['params']['kwargs'],
                             message['params']['kwargs'])
        self.assertItemsEqual(job.message['params']['args'],
                              message['params']['args'])
        self.assertEqual(job.state, models.Job.IN_QUEUE)

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.get_job')
    @mock.patch('beanstalkd.settings')
    def test_cancel_job_old_way(self, settings, get_job, connection):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'
        settings.DISABLE = False

        from .jobs_for_tests import do_something

        do_something(1, 2, 3, a=1, b=2, c=3)

        self.assertEqual(models.Job.objects.count(), 1)
        job = models.Job.objects.all()[0]
        get_job.return_value = mock.Mock()
        get_job.return_value.jid = job.beanstalk_id
        get_job.return_value.body = pickle.dumps(
            {
                # 'db_job_id': job.id,
                'name': u'tests.jobs_for_tests.do_something',
                'params': {
                    'args': (1, 2, 3),
                    'kwargs': {
                        'a': 1,
                        'b': 2,
                        'c': 3,
                    }
                }
            }
        )
        self.assertEqual(models.Job.objects.count(), 1)
        job_id = job.beanstalk_id

        from beanstalkd import get_proxy

        connection_proxy = get_proxy()
        connection_proxy.finish(job_id)

        get_job.return_value.delete.assert_called_once_with()
        self.assertEqual(models.Job.objects.complete().count(), 1)

    def build_get_job_mock(self, get_job, job, old=True):
        get_job.return_value = mock.Mock()
        get_job.return_value.jid = job.beanstalk_id
        body = {
            'name': u'tests.jobs_for_tests.do_something',
            'params': {
                'args': (1, 2, 3),
                'kwargs': {
                    'a': 1,
                    'b': 2,
                    'c': 3,
                }
            }
        }
        if not old:
            body['db_job_id'] = job.id

        get_job.return_value.body = pickle.dumps(
            body
        )

        return body

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.get_job')
    @mock.patch('beanstalkd.settings')
    def test_query_count(self, settings, get_job, connection):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'
        settings.DISABLE = False

        from .jobs_for_tests import do_something

        # cold
        with self.assertNumQueries(6):
            do_something(1, 2, 3, a=1, b=2, c=3)

        models.Job.objects.delete()

        # warm
        with self.assertNumQueries(3):
            do_something(1, 2, 3, a=1, b=2, c=3)
        job = models.Job.objects.all()[0]
        self.build_get_job_mock(get_job, job, False)

        from beanstalkd import get_proxy

        connection_proxy = get_proxy()

        with self.assertNumQueries(3):
            connection_proxy.finish(job.beanstalk_id)

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.get_job')
    @mock.patch('beanstalkd.settings')
    def test_cancel_job_new_way(self, settings, get_job, connection):
        settings.JOBS_CONF_NAME = 'tests/test_jobs.yaml'
        settings.DISABLE = False

        from .jobs_for_tests import do_something

        do_something(1, 2, 3, a=1, b=2, c=3)

        self.assertEqual(models.Job.objects.count(), 1)
        job = models.Job.objects.all()[0]

        self.build_get_job_mock(get_job, job, False)

        self.assertEqual(models.Job.objects.count(), 1)
        job_id = job.beanstalk_id

        from beanstalkd import get_proxy

        connection_proxy = get_proxy()

        connection_proxy.finish(job_id)

        get_job.return_value.delete.assert_called_once_with()
        self.assertEqual(models.Job.objects.complete().count(), 1)

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.settings')
    def test_unique_job(self, settings, connection):
        settings.JOBS_CONF_NAME = 'tests/test_unique_jobs.yaml'
        settings.DISABLE = False

        from .jobs_for_tests import do_something_unique

        models.Job.objects.delete()

        do_something_unique(1, 2, 3, a=1, b=2, c=3)
        do_something_unique(1, 2, 3, a=1, b=2, c=3)
        do_something_unique(1, 2, 3, a=1, b=2, c=3)

        self.assertEqual(models.Job.objects.count(), 1)

    def __perform_mocked_job(self, job):
        connection = mock.Mock()
        connection.reserve = mock.Mock()
        connection.reserve.return_value = job
        w = Worker()
        w.connection = connection
        w.initialize_connection = mock.Mock()
        w.initialize_connection.return_value = connection
        w.perform_job()

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.settings')
    @utils.override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_non_silent_job(self, settings, connection):
        settings.JOBS_CONF_NAME = 'tests/test_unique_jobs.yaml'
        settings.DISABLE = False

        models.Job.objects.delete()

        self.assertEqual(len(mail.outbox), 0)

        job = mock.Mock()
        job.body = pickle.dumps({
            'name': u'tests.jobs_for_tests.do_something_non_silently',
            'params': {
                'args': (1, 2, 3),
                'kwargs': {
                    'a': 1,
                    'b': 2,
                    'c': 3,
                }
            }
        })
        self.assertEqual(len(mail.outbox), 0)
        self.__perform_mocked_job(job)
        self.assertNotEqual(len(mail.outbox), 0)

    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.get_job')
    @mock.patch('beanstalkd.beanstalk_proxy.BeanstalkProxy.connection')
    @mock.patch('beanstalkd.settings')
    @utils.override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_silent_job(self, settings, connection, get_job):
        settings.JOBS_CONF_NAME = 'tests/test_unique_jobs.yaml'
        settings.DISABLE = False

        models.Job.objects.delete()


        job = mock.Mock()
        job.body = pickle.dumps({
            'name': u'tests.jobs_for_tests.do_something_silently',
            'params': {
                'args': (1, 2, 3),
                'kwargs': {
                    'a': 1,
                    'b': 2,
                    'c': 3,
                }
            }
        })
        self.assertEqual(len(mail.outbox), 0)
        self.__perform_mocked_job(job)
        self.assertEqual(len(mail.outbox), 0)
