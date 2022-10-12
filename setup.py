"""Setup file for reasoner-validator package."""
from setuptools import setup

with open("README.md", "r") as stream:
    long_description = stream.read()

NAME = 'reasoner-validator'

# Significant API change with respect to validation messaging
VERSION = '3.0.5'

DESCRIPTION = 'Validation tools for Reasoner API'
URL = 'https://github.com/NCATSTranslator/reasoner-validator'

# Patrick Wang, project creator and emeritus Translator scientist
AUTHOR = 'Richard Bruskiewich, Patrick Wang'

EMAIL = 'richard.bruskiewich@delphinai.com'
REQUIRES_PYTHON = '>=3.8'
LICENSE = 'MIT'

setup(
    name=NAME,
    author=AUTHOR,
    version=VERSION,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    description="Validation tools for Reasoner API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=[
        "reasoner_validator",
        "reasoner_validator.biolink",
        "reasoner_validator.sri",
        "reasoner_validator.trapi"
    ],
    package_data={},
    include_package_data=True,
    install_requires=[
        "jsonschema",
        "pyyaml",
        "requests",
        "linkml-runtime>=1.3.1",
        "linkml>=1.3.2",
        "prefixcommons==0.1.11",
        "tomli<2.0.0,>=0.2.6",
        "bmt==0.8.4"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
    zip_safe=False
)
