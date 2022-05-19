"""Setup file for reasoner-validator package."""
from setuptools import setup

with open("README.md", "r") as stream:
    long_description = stream.read()

setup(
    name="reasoner-validator",
    version="2.2.2",
    # Patrick Wang, project creator and emeritus Translator scientist
    author="Richard Bruskiewich, Patrick Wang",  # current maintainer
    author_email="richard.bruskiewich@delphinai.com, patrickelvin@gmail.com",
    url="https://github.com/NCATSTranslator/reasoner-validator",
    description="Validation tools for Reasoner API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["reasoner_validator", "reasoner_validator.biolink"],
    package_data={},
    include_package_data=True,
    install_requires=[
        "jsonschema>=3.0,<4.0",
        "pyyaml>=5.1,<6.0",
        "requests>=2.0,<3.0",
    ],
    zip_safe=False,
    license="MIT",
    python_requires=">=3.7",
)
