import os
import re
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'src', 'mbfxml2ex', '__init__.py')) as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

# Get the long description from the README file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

dependencies = ['opencmiss.zinc', 'opencmiss.utils >= 0.2.0']


setup(
    name="mbfxml2ex",
    version=version,
    author="Auckland Bioengineering Institute",
    author_email="h.sorby@auckland.ac.nz",
    description="Python client for generating Ex format model descriptions from MBF XML.",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    packages=find_packages("src"),
    package_dir={"": "src"},
    zip_safe=False,
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'mbfxml2exconverter=mbfxml2ex.app:main',
        ]
    },
    license="Apache Software License",
    keywords="MBF OpenCMISS-Zinc",
    url="https://github.com/hsorby/mbfxml2ex",
    download_url="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Utilities",
    ],
)
