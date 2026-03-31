#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PanDoG - Setup Script
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='pandog',
    version='0.0.1',
    description='Accessible cross-platform Pandoc GUI',
    long_description=read_file('README.md') if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    author='Steffen Schultz',
    author_email='steffenschultz@mailbox.org',
    url='https://github.com/schulle4u/pandog',
    license='MIT',

    packages=find_packages(where='src'),
    package_dir={'': 'src'},

    include_package_data=True,
    package_data={
        '': ['locale/*/LC_MESSAGES/*.mo'],
    },

    install_requires=[
        'wxPython>=4.2.0',
    ],

    python_requires='>=3.10',

    entry_points={
        'console_scripts': [
            'pandog=main:main',
        ],
        'gui_scripts': [
            'pandog-gui=main:main',
        ],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: File Formats',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Operating System :: OS Independent',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Environment :: MacOS X',
    ],

    keywords='Pandoc Converter Markdown HTML Ebook',

    project_urls={
        'Bug Reports': 'https://github.com/schulle4u/pandog/issues',
        'Source': 'https://github.com/schulle4u/pandog',
    },
)
