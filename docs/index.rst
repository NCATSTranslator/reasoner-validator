Reasoner Validator
==================

This Python module provides the :code:`validate()` method for validating any component *in any version* of the
`Translator Reasoner API (TRAPI) <https://github.com/NCATSTranslator/ReasonerAPI/blob/master/TranslatorReasonerAPI.yaml>`_.

.. code-block:: python

    from reasoner_validator import validate
    message = ...
    try:
      validate(message, "Message", "1.1.0")
    except ValidationError:
      raise ValueError('Bad TRAPI component!')

.. toctree::
   :maxdepth: 1
   :hidden:

   reasoner_validator

Installation
------------

.. code-block:: bash

  pip install reasoner-validator

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

