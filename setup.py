#!/usr/bin/env python
from setuptools import setup, find_packages
import os
import glob
import re
version = None
package_name = "pyconfigmanager"
os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('{}/version.py'.format(package_name)) as version_file:
    exec(version_file.read())

requirements = [
    'PyYaml',
]
dependency_links = [
    """git+https://github.com/miacro/{}.git@master#egg={}-9999""".format(
        package_name, package_name)
]
dependency_links = []


def get_scripts():
    result = []
    for item in glob.glob("{}/bin/*".format(package_name)):
        if os.access(item, os.X_OK):
            result.append(item)
    return result


def get_package_data():
    directory = package_name
    return [
        filename
        for ext in ("json", "yaml") for filename in glob.glob(
            os.path.join(directory, "**", "*.{}".format(ext)), recursive=True)
        if all(
            re.match(os.path.join(directory, pattern, ".*"), filename) is None
            for pattern in ("test", "tests"))
    ]


long_description = ''
setup(
    name=package_name,
    version=version,
    description=package_name,
    long_description=long_description,
    url='',
    author='miacro',
    author_email='fqguozhou@gmail.com',
    maintainer='miacro',
    maintainer_email='fqguozhou@gmail.com',
    packages=find_packages(exclude=['test.*', 'test', 'tests.*', 'tests']),
    install_requires=requirements,
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
    ],
    scripts=get_scripts(),
    ext_modules=[],
    package_data={package_name: get_package_data()},
    dependency_links=dependency_links,
)
