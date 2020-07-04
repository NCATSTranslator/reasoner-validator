"""Setup file for reasoner-validate package."""
from setuptools import setup

setup(
    name='reasoner-validate',
    version='0.1.0-dev',
    author='Patrick Wang',
    author_email='patrick@covar.com',
    url='https://github.com/NCATS-Gamma/robokop-messenger',
    description='Validation tools for Reasoner API',
    packages=['reasoner_validate', 'reasoner_validate.data'],
    package_data={'reasoner_validate.data': ['*.yaml']},
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    python_requires='>=3.6',
)
