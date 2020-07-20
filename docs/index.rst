Reasoner Validator
==================

The Reasoner validator will allow you to validate Reasoner API components.

Look how easy it is to use:

.. code-block:: python

    from reasoner_validate import validate_Message, ValidationError
    message = ...
    try:
      validate_Message(message)
    except ValidationError:
      raise ValueError('Bad Reasoner component!')

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   reasoner_validate

Features
--------

- Be awesome
- Make things faster

Installation
------------

Install $project by running:

    install project

Contribute
----------

- Issue Tracker: github.com/$project/$project/issues
- Source Code: github.com/$project/$project

Support
-------

If you are having issues, please let us know.
We have a mailing list located at: project@google-groups.com

License
-------

The project is licensed under the MIT license.

