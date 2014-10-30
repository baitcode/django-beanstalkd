from beanstalkd import job, exceptions


def for_check_mocking(*args, **kwargs):
    pass


@job
def do_something(*args, **kwargs):
    for_check_mocking(*args, **kwargs)


@job
def do_something_unique(*args, **kwargs):
    for_check_mocking(*args, **kwargs)

@job
def do_something_silently(*args, **kwargs):
    for_check_mocking(*args, **kwargs)
    raise exceptions.SilentFailException('Ha you momma so fat!')

@job
def do_something_non_silently(*args, **kwargs):
    for_check_mocking(*args, **kwargs)
    raise Exception('Ha you momma so fat!')