# Change Log

The Reasoner Validator package is evolving along with progress in TRAPI and Biolink Model standards within the NCATS Biomedical Knowledge Translator. 

## v3.4.14

- Set default of compact_format to 'True' and title=None (suppress), in dumps() output.
- BMT upgraded to 1.0.8

## v3.4.13

- Added the ValidationReporter.dumps() method which directly returns the string created by ValidationReporter.dump() but without the need for an explicit file device

## v3.4.12

- added validation to explicitly detect presence of at least one concrete (non-abstract, non-mixin) category in categories list
- refactored the codes.yaml code both to fix validation code deficiencies, distinctly record validation context, and to simplified template messages
- finalized a first release of 'dump()',  a significantly enhanced human-readable text report formatter for validation code associated messages
- refactored versioning.py package for simplicity and correct management of prereleases (like 1.4.0-beta)
- preliminary refactoring of unit tests in anticipation of TRAPI 1.4.0 testing and package updates

## v3.4.11

- added some code inadvertently not committed in v3.4.10.
- fixed various validation codes including swapping 'identifier' indexing for reduced redundancy
- enhanced dumping of human-readable messages for validation
 
## v3.4.10

- reasoner_validator.biolink.BiolinkValidator.validate_category()  now only returns a non-None value if it is a 'concrete' category, and reports 'unknown' or 'missing' (None or empty string) category names as errors; deprecated categories are reported as warnings; but both 'mixin' and 'abstract' categories are accepted as valid categories silently ignored, but are not considered 'concrete', thus the method returns None. Bottom line is when at least one valid 'concrete' `category` is provided in the subject/object category input edges, or categories list for TRAPI query or knowledge graphs, and if all identifiers provided have a namespace recorded in the `id_prefix` slot list of at least one provided 'concrete' category, then the edge categories and ids will properly validate.
 
## v3.4.9

- Split the qualifier validation reporting into distinct codes for the qualifier_type_id ("**qualifier.type_id.unknown**") versus `qualifier_value` ("**qualifier.value.unresolved**")
- `ars_uuid_result_test_runner.py` made slightly more user friendly

## v3.4.8

- Python dependency conflict between bmt and pytest fixed. 3.4.7 patched and reissued as v3.4.8
 
## v3.4.7

- `ars_uuid_result_test_runner.py` access generalized to poll available ARS servers
- Upgrade BMT to 1.0.3 - may fix some misleading validation results
 
## v3.4.6

- 'edge_limit' knowledge graph threshold argument added to `TRAPIResponseValidator.check_compliance_of_trapi_response` method
- cleaned up a bit of technical debt
 
## v3.4.5

- Missing 'primary_knowledge_source' now reported as an error
- 'primary_knowledge_source' value cardinality > 1 is reported as a warning
- made attribute validation context more explicit (with the edge identifier, now used as indexing identifier of message templates)
 
## v3.4.4

- Added in attribute Type Id validation codes that were missing for 'generic' element filters
 
## v3.4.3

- Fixed some failing unit tests and some minor technical debt
- Reversed v3.4.1 commenting out of TRAPIResponseValidator.sanitize_trapi_query but added validation warnings for null field values for workflow step 'parameters' or 'runner_parameters' 

## v3.4.2

- Fixed missing or misaligned codes.yaml validation codes
- Added the `ars_uuid_result_test_runner.py` script which runs CLI validation against an ARS UUID indexed TRAPI Responses

## v3.4.1

- Bug fix in TRAPIResponseValidator.sanitize_trapi_query (despite bug fix, commented out use of this method pending further evidence of KP/ARA non-compliance with the workflow schema)

## v3.4.0

- This is a slightly disruptive 'minor' (not 'patch') release in that the internal and exported (JSON) validation message format is evolving.
- Here, an additional level of internal validation message redesign was attempted to substantially reduce duplication in reported validation messages. 
- To achieve the above, if templated messages in codes.yaml have one or more parameter fields, then the first such field must be called 'identifier' and be a message discriminating string field. Other parameters may be added to the template but these are not (yet) guaranteed to avoid duplication in reporting. The string value of a message 'identifier' field is internally used as keys to index messages under the given code identifier. See the library methods for details.

## v3.3.3

- update and clean up of web API Dockerfile

## v3.3.2

- Upgrade Python dependency to ^3.9 (BMT driven requirement)
- Upgrade Biolink Model Toolkit (BMT) to 1.0.2 to gain access to latest Biolink 3 qualifier validation methods
- Relatively full implementation of the Query Graph qualifier_constraints and Knowledge Graph qualifiers validation
- Added some new and repaired some existing validation codes and unit tests - all unit tests pass (TRAPI 1.3 and Biolink 3.2.0)

## v3.3.1

- updated root project README with correct examples of new ValidationReporter JSON output
- initial code to (partly) validate Biolink 3 edge qualifiers (still more work needed once Biolink Model Toolkit support for validation is available)

## v3.3.0

- ValidationReporter internal message format recoded to avoid message duplication; repeated reporting of a given code is now indexed into a single list of error message parameters; Conversely, 'display()' methods now return lists of decoded messages.
- Added 'branch' version access to TRAPI schemata
- Make Biolink element deprecate/abstract/mixin non-strict validation less severe
- Fixed Biolink model compliance unit tests to pass Biolink release 3.1.1, but 'qualifiers' not yet implemented.
- KGX, BMT and LinkML updated to latest.
- Note: poetry installation under MS Windows seems broken at the moment (thorny pywin32 dependency conflict). The project runs successfully under WSL2/Ubuntu (if you are Windoze challenged).

## v3.2.4
- fixed scoping of TRAPI Response validator method to include more than just the message (i.e. workflows, etc.)

## v3.2.3
- cleaned up validation codes, especially with respect to predicates

## v3.2.2
- added validation message descriptions to the codes.yaml file
- added additional validation codes
- renamed yaml path for some codes for semantic clarity
- update project 'ReadTheDocs' documentation including generation of page of code descriptions

## v3.2.1
- pyproject.toml patch to fix configuration bug

## v3.2.0

- Project converted to use **poetry** dependency management
- Some structural changes to project (Sphinx) documentation
- Added markdown generator for reading codes.yaml as a Markdown document in the project documentation.
- Created this formal CHANGLOG.md!

## v3.1.5

Enforce kgx upgrade to >=1.6.0 (to accommodated recent linkml dependencies) 

## v3.1.4

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
