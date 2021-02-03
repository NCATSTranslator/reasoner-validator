"""Setup file for reasoner-validator package."""
from setuptools import setup

with open('README.md', 'r') as stream:
    long_description = stream.read()

setup(
    name='reasoner-validator',
    version='1.0.2.1.0.1',
    author='Patrick Wang',
    author_email='patrick@covar.com',
    url='https://github.com/NCATSTranslator/reasoner-validator',
    description='Validation tools for Reasoner API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['reasoner_validator', 'reasoner_validator.data'],
    package_data={'reasoner_validator.data': ['*.yaml']},
    include_package_data=True,
    install_requires=[
        'jsonschema>=3.0',
        'pyyaml>=5.1',
        "importlib_resources ; python_version<'3.7'",
    ],
    zip_safe=False,
    license='MIT',
    python_requires='>=3.6',
)
