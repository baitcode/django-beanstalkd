from . import tubes, models, beanstalk_proxy
from .decorator import job
from exceptions import *

__version__ = '0.9.0'
__title__ = 'beanstalkd'
__author__ = 'Ilia Batii'
__license__ = 'Apache 2.0'


def get_proxy():
    return beanstalk_proxy.BeanstalkProxy()
