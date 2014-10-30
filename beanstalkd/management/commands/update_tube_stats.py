from django.core.management import BaseCommand
from beanstalkd import tubes, models, get_proxy


class UpdateTubeStatsCommand(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()
        self.children = []
        self.db_tubes = []

    def handle(self, *args, **options):
        b = get_proxy()

        for tube in tubes.as_list():
            tube, created = models.Tube.objects.get_or_create(
                name=tube
            )
            self.db_tubes.append(tube)
            b.update_tube_stats(tube.name)


Command = UpdateTubeStatsCommand
