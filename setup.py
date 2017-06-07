# coding: utf-8
# Author: Allen Zou
# 2017/4/15 下午10:13

from setuptools import setup
from sql_builder import __version__

setup(
    name='sql-builder',
    version=".".join(str(x) for x in __version__),
    description='A builder for SQL statement',
    url='https://github.com/it-allen/sql-builder',
    author='Allen Zou',
    author_email='zyl_work@163.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='sql',
    packages=['sql_builder']
)
