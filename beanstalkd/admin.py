from django.contrib import admin
from django.contrib import messages
from beanstalk import models, get_proxy, tubes, settings


def delete_job(modeladmin, request, queryset):
    proxy = get_proxy()

    for job in queryset:
        if not job.is_complete and not job.is_failed:
            proxy.finish(job.beanstalk_id)
            msg = u'Job {} is processed'
            messages.info(request, msg.format(
                job.id
            ))
            continue

        msg = u'Job {} already complete or failed'
        messages.error(request, msg.format(
            job.id
        ))

delete_job.short_description = 'Finish job'


def bury_job(modeladmin, request, queryset):
    proxy = get_proxy()
    for job in queryset:
        if job.is_delayed:
            msg = u'Job {} is delayed, cannot bury it.'
            messages.error(request, msg.format(job.id))
            continue

        if not job.is_complete:
            proxy.bury(job.beanstalk_id)
            msg = u'Job {} is processed'
            messages.info(request, msg.format(job.id))
            continue

        msg = u'Job {} already complete'
        messages.error(request, msg.format(
            job.id
        ))
bury_job.short_description = 'Bury job'


def kick_job(modeladmin, request, queryset):
    proxy = get_proxy()
    for job in queryset:
        if job.is_buried:
            proxy.kick(job.beanstalk_id)
            msg = u'Job {} is processed'
            messages.info(request, msg.format(
                job.id
            ))
            continue

        msg = u'Job {} is not buried. Cannot kick it.'
        messages.error(request, msg.format(
            job.id
        ))

kick_job.short_description = 'Kick job'


def restart_job(modeladmin, request, queryset):
    proxy = get_proxy()
    for job in queryset:
        if job.is_complete or job.is_failed:
            message = job.message
            tube_settings = tubes.get_tube_conf(message['name'])
            default_delay = settings.DEFAULT_RETRY_DELAY
            proxy.put(
                message['name'],
                message,
                tube_settings.get('retry_delay', default_delay)
            )
            msg = u'Job {} is restarted'
            messages.info(request, msg.format(
                job.id
            ))
            continue

        msg = u'Job {} is not complete or failed. Cannot restart it.'
        messages.warning(request, msg.format(
            job.id
        ))

restart_job.short_description = 'Restart job'


class JobAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'beanstalk_id',
        'tube_name',
        'state',
        'created_at',
        'updated_at',
    ]

    date_hierarchy = 'created_at'

    actions = [
        delete_job,
        bury_job,
        kick_job,
        restart_job,
    ]

    list_filter = [
        'tube',
        'state'
    ]


admin.site.register(models.Tube)
admin.site.register(models.Job, JobAdmin)
