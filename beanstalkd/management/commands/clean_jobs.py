from django.core.management import BaseCommand
from beanstalk import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        models.Job.objects.complete().old().delete()
        models.Job.objects.unknown().old().delete()
