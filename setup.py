import setuptools
from os.path import join, dirname

import beanstalkd


setuptools.setup(
    name="",
    version=beanstalkd.__version__,
    packages=["beanstalkd"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=open(join(dirname(__file__), 'requirements.txt')).readlines(),
    tests_require=[
        'django<1.8',
    ],
    test_suite='runtests.runtests',
    author="baitcode",
    author_email="batiyiv@gmail.com",
    url="http://github.com/batiyiv/django-beanstalkd",
    license="Apache 2.0",
    description="Beanstalkd monitoring and management solution.",
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    keywords="django beanstalkd monitoring queue job scheduling admin",
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
