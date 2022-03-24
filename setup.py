# Copyright 2022 Krono-Safe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Installation script"""

import pathlib
from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='rsfstat',
    version='1.0.0',
    description='Compute statistics on an ASTERIOS static scheduling plan (RSF)',

    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/krono-safe/rsfstat',

    author='Krono-Safe R&D Team',
    author_email='contact@krono-safe.com',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: 3.10",
        'Programming Language :: Python :: 3 :: Only',
    ],

    packages=find_packages(where='rsfstat'),
    package_dir={'': 'rsfstat'},
    py_modules=['rsfstat'],

    python_requires='>=3.7, <4',
    install_requires=[
        'flatbuffers==2.0',
        'colorama==0.4.4',
    ],

    extras_require={
        'dev': ['pylint', 'pytest', 'bump2version'],
    },

    entry_points={
        'console_scripts': [
            'rsfstat=rsfstat:main',
        ],
    },
)
