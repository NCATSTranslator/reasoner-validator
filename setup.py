"""Setup file for reasoner-validate package."""
from setuptools import setup

setup(
    name='reasoner-validate',
    version='0.1.0-dev',
    author='Patrick Wang',
    author_email='patrick@covar.com',
    url='https://github.com/NCATSTranslator/reasoner-validate',
    description='Validation tools for Reasoner API',
    packages=['reasoner_validate', 'reasoner_validate.data'],
    package_data={'reasoner_validate.data': ['*.yaml']},
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
