# Change Log

The Reasoner Validator package is evolving along with progress in TRAPI and Biolink standards within the NCATS Biomedical Knowledge Translator. 

### v3.3.0

- ValidationReporter internal message format recoded to avoid message duplication; repeated reporting of a given code is now indexed into a single list of error message parameters; Conversely, 'display()' methods now return lists of decoded messages.
- Added 'branch' version access to TRAPI schemata
- Make Biolink element deprecate/abstract/mixin non-strict validation less severe
- Fixed Biolink model compliance unit tests to pass Biolink release 3.1.1

### v3.2.4
- fixed scoping of TRAPI Response validator method to include more than just the message (i.e. workflows, etc.)

### v3.2.3
- cleaned up validation codes, especially with respect to predicates

### v3.2.2
- added validation message descriptions to the codes.yaml file
- added additional validation codes
- renamed yaml path for some codes for semantic clarity
- update project 'ReadTheDocs' documentation including generation of page of code descriptions

### v3.2.1
- pyproject.toml patch to fix configuration bug

### v3.2.0

- Project converted to use **poetry** dependency management
- Some structural changes to project (Sphinx) documentation
- Added markdown generator for reading codes.yaml as a Markdown document in the project documentation.
- Created this formal CHANGLOG.md!

### v3.1.5

Enforce kgx upgrade to >=1.6.0 (to accommodated recent linkml dependencies) 

### v3.1.4

Inject more graph validation context into codes; leverage this context in message management and generation. Unit tests all fixed.

## v3.1.1

Fix python dependencies in setup.py.

## v3.1.0

This release has the full commitment to the Biolink Model Toolkit 0.8.12 release, which also defaults the Biolink Model validation to the latest release 3.0.* of the schema.

This doesn't mean that the 2.4.8 and lower Biolink Models won't be substantially validated correctly, but simply that one will expect a few spurious validation errors against such releases. One known spurious error is in the incorrect validation of 'non_canonical' predicates (i.e. canonical will be reported as `non_canonical`...).  

## v3.0.0

This major release of the reasoner-validator centers around a **ValidationReporter** (Python) class wrapping all validation messages and supporting detection calls.  This particular latest iteration also injects more context into the validation message codes (as a [master YAML file with hierarchically-indexed Python string templates](reasoner_validator/codes.yaml)).

The underlying code validates TRAPI responses (using _jsonschema_) against the TRAPI _ReasonerAPI.yaml_ data model and orthogonally validates Biolink Model compliance of the internal content of such responses.  

A given validation targets TRAPI and Biolink Model releases as specified by user parameter or by default (generally, with default versions TRAPI 1.3 and Biolink Model (default assumed by Biolink Model Toolkit).

## v2.2.14

Final release with the simple string validation messaging forma.

## v2.2.1-13

Various iterations of refinement of Biolink validation

## v2.2.0

- Biolink model validation
- Added FastApi and Swagger interface.
- Validation returning a flat dictionary of arcane string messages.
- Dockerized validator service

## Earlier 2.#.# releases

Had a simple base TRAPI schema 'validate' with errors throwing a Python exception; 

## 1.* releases

Preliminary releases of the validation code, now obsolete.
