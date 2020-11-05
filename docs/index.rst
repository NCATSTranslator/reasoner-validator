Reasoner Validator
==================

This Python module provides a :code:`validate_X()` method for each component in the
`Reasoner API <https://github.com/NCATSTranslator/ReasonerAPI/blob/master/TranslatorReasonerAPI.yaml>`_.

.. code-block:: python

    from reasoner_validator import validate_Message, ValidationError
    message = ...
    try:
      validate_Message(message)
    except ValidationError:
      raise ValueError('Bad Reasoner component!')

.. toctree::
   :maxdepth: 1
   :hidden:

   reasoner_validator

Installation
------------

.. code-block:: bash

  pip install reasoner-validator


To install the validator for a specific version of the Reasoner API, e.g. 0.9.2:

.. code-block:: bash

  pip install reasoner-validator==0.9.2.*

Note the trailing :code:`.*`; the validator library version follows the schema version,
so 0.9.2.1.0.0 indicates schema version 0.9.2 and library version 1.0.0.

Contribute
----------

- `Report a bug <https://github.com/NCATSTranslator/reasoner-validator/issues/new?template=bug_report.md>`_
- `Request a feature <https://github.com/NCATSTranslator/reasoner-validator/issues/new?template=feature_request.md>`_

Support
-------

- `Ask a question <https://github.com/NCATSTranslator/reasoner-validator/issues/new?template=question.md>`_

License
-------

The project is licensed under the MIT license.

