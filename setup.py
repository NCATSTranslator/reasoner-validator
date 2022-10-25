"""Setup file for reasoner-validator package."""
from setuptools import setup

with open("README.md", "r") as stream:
    long_description = stream.read()

NAME = 'reasoner-validator'

# Significant API change from release 3.0.0 with respect to validation messaging
# Release 3.1.* targets Biolink Model 3.0.3 or later for optimal validation.
# Validation of Biolink Model releases < 3.0.5 may report a few spurious validation errors.
# This is due to non-backward compatible behaviour of the
# Biolink Model Toolkit, not the validation software per say.
VERSION = '3.1.4'

DESCRIPTION = 'Validation tools for Reasoner API'
URL = 'https://github.com/NCATSTranslator/reasoner-validator'

# Patrick Wang, project creator and emeritus Translator scientist
AUTHOR = 'Richard Bruskiewich, Patrick Wang'

EMAIL = 'richard.bruskiewich@delphinai.com'
REQUIRES_PYTHON = '>=3.8'
LICENSE = 'MIT'

with open("requirements.txt", "r") as FH:
    REQUIREMENTS = FH.readlines()

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
    install_requires=[r for r in REQUIREMENTS if not r.startswith("#")],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
    zip_safe=False
)
