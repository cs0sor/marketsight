#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'suds==0.4',
    'wsgiref==0.1.2'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='marketsight',
    version='0.1.0',
    description="simple python wrapper round marketsight API",
    long_description=readme + '\n\n' + history,
    author="Simon Oram",
    author_email='simon@electrosoup.co.uk',
    url='https://github.com/cs0sor/marketsight',
    packages=[
        'marketsight'
    ],
    package_dir={'marketsight':
                 'marketsight'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='marketsight',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
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
    tests_require=test_requirements
)
