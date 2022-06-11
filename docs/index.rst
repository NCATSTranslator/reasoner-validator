Reasoner Validator
==================

This Python module provides the :code:`validate()` method for validating any component *in any version* of the
`Translator Reasoner API (TRAPI) <https://github.com/NCATSTranslator/ReasonerAPI/blob/master/README.md>`_ and `Biolink Model <https://github.com/biolink/biolink-model/blob/master/README.md>`_.

.. code-block:: python

    from reasoner_validator import validate
    message = ...
    try:
      validate(
            instance=message,
            component="Message",
            trapi_version="1.2.0"
      )
    except ValidationError:
      raise ValueError('Bad TRAPI component!')

.. toctree::
   :maxdepth: 2

   TRAPI <reasoner_validator>
   Biolink <reasoner_validator.biolink>

Installation
------------

.. code-block:: bash

  pip install reasoner-validator

Validator as a Web Service
--------------------------

The service may be run directly as a python module. It is suggested that a virtual environment first be created (using virtualenv, conda, within your IDE, or equivalent).  Then, certain Python dependencies need to be installed, as follows:

.. code-block:: bash

    pip install -r requirements-service.txt


The module may afterwards be run, as follows:

.. code-block:: bash

    python -m app.main


See `project README for full details <https://github.com/NCATSTranslator/reasoner-validator/blob/master/README.md>`_

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

