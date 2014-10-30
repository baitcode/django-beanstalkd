import datetime
import hashlib
import pickle

from django.db import models
from django.db.models.query import QuerySet
from django_extensions.db.fields.json import JSONField
from model_utils.managers import PassThroughManager

from . import settings


class Tube(models.Model):
    name = models.CharField(max_length=1000)
    buried = models.IntegerField(null=True)
    delayed = models.IntegerField(null=True)
    ready = models.IntegerField(null=True)
    reserved = models.IntegerField(null=True)
    urgent = models.IntegerField(null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        db_table = 'beanstalk_tube'


class JobQuerySet(QuerySet):
    def unknown(self):
        return self.exclude(
            state__in=[state_id for state_id, state_name in Job.STATES]
        )

    def complete(self):
        return self.filter(
            state=Job.COMPLETE
        )

    def old(self):
        now = datetime.datetime.utcnow()
        old_job_age = settings.OLD_JOB_AGE
        return self.filter(
            created_at__lte=now - old_job_age
        )

    def buried(self):
        return self.filter(
            state=Job.BURIED
        )

    def in_queue(self):
        return self.filter(
            state=Job.IN_QUEUE
        )


class Job(models.Model):
    IN_QUEUE = 1
    BURIED = 2
    COMPLETE = 3
    PROCESSING = 4
    DELAYED = 5
    FAILED = 6
    STATES = (
        (IN_QUEUE, 'in queue'),
        (BURIED, 'buried'),
        (COMPLETE, 'complete'),
        (PROCESSING, 'processing'),
        (DELAYED, 'delayed'),
        (FAILED, 'failed'),
    )
    beanstalk_id = models.IntegerField()
    instance_ip = models.IPAddressField()
    instance_port = models.IntegerField()
    tube = models.ForeignKey('beanstalkd.Tube', null=True)
    tube_name = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True, auto_created=True)
    updated_at = models.DateTimeField(auto_now=True)
    digest = models.CharField(max_length=32, null=True)
    message = JSONField()

    state = models.SmallIntegerField(choices=STATES, default=IN_QUEUE)

    objects = PassThroughManager.for_queryset_class(JobQuerySet)()

    @property
    def is_complete(self):
        return self.state == self.COMPLETE

    @property
    def is_delayed(self):
        return self.state == self.DELAYED

    @property
    def is_buried(self):
        return self.state == self.BURIED

    @property
    def is_failed(self):
        return self.state == self.FAILED

    @classmethod
    def get_message_digest(cls, message):
        message_for_digest = message.copy()
        message_for_digest.pop('db_job_id', None)
        m = hashlib.md5()
        m.update(pickle.dumps(message_for_digest))
        return m.hexdigest()

    def save(self, *args, **kwargs):
        tube = self.tube

        if not tube:
            self.tube, _ = Tube.objects.get_or_create(name=self.tube_name)

        self.digest = Job.get_message_digest(self.message)
        return super(Job, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{} {}'.format(self.tube_name, self.beanstalk_id)

    class Meta:
        index_together = [
            ['digest', ]
        ]
        db_table = 'beanstalk_job'
