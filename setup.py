import os
import re
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'src', 'neurolucidaxml2ex.py')) as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

# Get the long description from the README file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

reqs = ['opencmiss.zinc']

print(find_packages("src"))

setup(
    name="neurolucidaxml2ex",
    version=version,
    author="Auckland Bioengineering Institute",
    author_email="h.sorby@auckland.ac.nz",
    description="Python client for generating Ex format model descriptions from Neurolucida XML.",
    long_description=long_description,
    py_modules=["neurolucidaxml2ex"],
    package_dir={"": "src"},
    zip_safe=False,
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'neurolucidaxml2exconverter=neurolucidaxml2ex:main',
        ]
    },
    license="",
    keywords="Neurolucida OpenCMISS-Zinc",
    url="https://github.com/hsorby/neurolucidaxml2ex",
    download_url="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Utilities",
    ],
)
