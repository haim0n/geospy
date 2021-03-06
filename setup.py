#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests', 'wifi', 'netifaces', 'sqlalchemy',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='geospy',
    version='0.1.0',
    description="Turn you Raspberry Pi to a Mobile GPS.",
    long_description=readme + '\n\n' + history,
    author="[1;5CHaim Daniel",
    author_email='haim.daniel@gmail.com',
    url='https://github.com/haim0n/geospy',
    packages=[
        'geospy',
    ],
    package_dir={'geospy': 'geospy'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='geospy',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'geospy = geospy.geospy:main'
        ]
    }
)
