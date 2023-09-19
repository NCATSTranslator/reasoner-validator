# Change Log

The Reasoner Validator package is evolving along with progress in TRAPI and Biolink Model standards within the NCATS Biomedical Knowledge Translator.

## 3.9.3
- Added (optional) OpenTelemetry functionality for web service.

## 3.9.2
- demoted **dangling nodes** 'error' down to 'warning' message, annotated with the list of missing nodes as the identifier

## 3.9.1
- Upgrade to Biolink Model Toolkit 1.1.2
- Removed all residual references to 'sanitize_trapi_response()' (warning: validation with pre-release versions of TRAPI 1.4 earlier than 1.4.2 may trigger some funny false positive validation messages)
- BiolinkValidator.PREDICATE_INCLUSIONS added (just with "biolink:interacts_with") to bypass 'mixin' Biolink Model validation error (pending full community review of the 'mixin' status of this predicate); unit tests modified to suit
- plus a small internal DRY refactor in test suit with respect to LATEST_BIOLINK_MODEL_VERSION

## 3.9.0
- Detect missing knowledge_graph names (resolves part of issue#35)
- detection of uninformative QNodes (resolve issue#14)
- Dangling ("unused") nodes detection is fully implemented (complements "edge nodes not in nodes list" detection already in place); resolves issue#74

## 3.8.10
- 'attribute_type_id' term which are Biolink (node) 'category' or (edge) 'predicate' terms generate a specific warning (not just a 'not an association slot' warning)
- Knowledge graph edge qualifiers qualifier "value unresolved" validation error demoted to a warning

# 3.8.9
- glitch while publishing to pypi.org

## 3.8.8
- "error.knowledge_graph.edge.attribute.value.empty" should NOT be triggered by numeric zeros either!

## 3.8.7
- Puzzling issue with validation of some qualifier values turned out to be a bug in the Biolink Model 3.5.2, resolved in 3.5.3, so fixed unit tests accordingly. This release doesn't have any core functional changes to the code but users of earlier versions should be aware that validation with Biolink Model releases earlier than 3.5.3 may give puzzling qualifier value validation messages.

## 3.8.6
- 'False' attribute values now properly handled; all other 'empty' values trigger an error message

## 3.8.5
- Add additional JSON element path context to "critical.trapi.validation" validation messages
- Remove TRAPI Response JSON sanitization, since TRAPI 1.4.2 is now the 'latest' and desired validation standard

## 3.8.4
- Non-destructive TRAPIResponseValidator.check_compliance_of_trapi_response(response) validation of TRAPI Response JSON (release 3.8.3 bug removed Message)

## 3.8.3
- Fixed TRAPI release management to cache TRAPI GitHub code release and branch tags locally - in a **versions.yaml** file - to avoid Git API calling denial of service issues; Small **scripts/trapi_release.py** utility script provided to update the **versions.yaml** file, as periodically necessary.
- YAML file management tech debt cleaned up a tiny bit. Tweaked a couple of validation codes for this reason.
- Added DEVELOPER_NOTES.md to guide uniform project release management (especially, of the esoteric bits of the project like TRAPI release and validation code updates)

## 3.8.2
- Removed `check_trapi_validity()` standalone API method to enforce a two-step process of instantiating a `TRAPISchemaValidator` instance then calling its `is_valid_trapi_query()` method.
- Spurious leading newline removed from TRAPI and Biolink Model validation version reporting log messages
- Fixed insidious edge source validation message reporting bug which masked all but the first of edges with a specified validation error
- Minor tweak to validation codes definitions to reduce duplication in reporting output or clarity of definition
- Fixed (and extended some) unit test cases related to all of the above.

## 3.8.1
- Generally repaired validation 'sources' ('source_trail') context recording to cover all applicable validation message cases (especially, edge 'qualifier' validation); tested with unit tests
- TRAPIGraphType class moved up the class/module hierarchy, alongside ValidatorReporter; strict_validation as Optional[bool] wrapped in the is_strict_validation() method which uses graph_type to decide on None default strictness (based on graph type)
- TRAPI and Biolink Model versions resolved now only reported in logger.info, not stderr
- only preset target_provenance in validator reporter constructors, not the various method signatures
- add 'categories' into edge context labels for reports (long lists of categories may be challenging here but ...)

## 3.8.0
- Internal class hierarchy restructured for logical clarity in recent releases, formally highlighted in this release
- Most visible TRAPIResponseValidator class (previously) moved from the **`reasoner_validator.__init__.py`** package module, into its own  **`reasoner_validator.validator`** module
- Some documentation repair

## 3.7.6
- TRAPI qualifier validation enhanced by use of biolink:Association subclass slot_usage driven constraints (leveraging novel Biolink Model Toolkit 1.1.1 methods)
- Validation made TRAPI Response (TRAPI) **`schema_version`** and **`biolink_version`** aware, taking precedence over default (non-overridden) values of these version parameters.

## 3.7.5
- Added TRAPI Response schema version and biolink version validation warning codes
- Warning about 'biolink:BiologicalCategory' and 'biolink:InformationContentEntity' are not issued if these categories are parent categories of concrete category instances specified in the 'categories' list

## 3.7.4
- resolves reasoner-validator issue 89 by validating semicolon delimited strings of infores

## 3.7.3
- Adding special override list for 'attribute_type_id' exceptions to stop error messages. This will apply to terms scheduled for implementation in a near term future Biolink Model release, but not yet out the door (but implemented proactively by early adopters within the Translator consortium). The initial list of such terms are the pre-Biolink Model version 3.5.0 terms 'biolink:knowledge_level' and 'biolink:agent_type'

## 3.7.2
- 'biolink:InformationContentEntity' added to exceptions only triggering a 'warning', not an 'error' validation message.
- Added the reasoner-validator version semver to the validation dump(s)

## 3.7.1
- JSONSCHEMA pinned to ~4.17.3 (implying <4.18.0 releases) for now, until we can figure out why the 4.18.0 causes the severe workflow schema access bug

## v3.7.0
- implementation of reasoner-validator issue #86 in which explicit validation error KP/ARA sources are reported in the validation. This change is sufficiently disruptive to the code methods and representation that 'minor' release of the repository is incremented to 3.7.
- to avoid confusion with new 'source' reporting, the pre-3.7 provenance 'sources' variable is renamed to 'target_provenance' and the variable localized directly into the BiolinkValidator constructor and included as parameter for pertinent high level method calls
- Use of Biolink node category "biolink:BiologicalCategory" which is abstract, now only triggers a validation warning, not an error. The 'exception' is currently hard coded into the validation (could have other categories added in this manner, if needed, later).

## v3.6.6
- code takes TRAPI 1.4.1 as the latest schema
- abstract out TRAPI versions a bit more and move TRAPI release constants to a global context
- further clean up of SemVer versioning code tech debt

## v3.6.5
- temporary TRAPI schema patch for validation correction
- clean out other technical debt

## v3.6.4
- Update Biolink Model Toolkit to 1.1.0 (implicit Biolink Model 3.5.0 update)

## v3.6.3
- 1.4.0 is now the full latest TRAPI release tracked by the code (for testing), but 1.4.0-beta code and unit tests being kept (for now)

## v3.6.2
- Various tweaks to the case 'test edge' validation code, to meet SRI Testing needs
- Split BiolinkValidator class into two parent parts, for ease of lightweight BMT wrapping reuse; for case edge validation, also look at predicate children (bullet proof validation against None BMT handle?)
- Add trapi error code for missing knowledge graph; tweak Response validation codes and docs
- Guarantee return of the original seed identifier when getting the list of aliases from Node Normalizer

## v3.6.1
- Reversed order of codes in codes.yaml resulting in new documentation order: Critical at top, Information at the bottom
- Fixed bug with SemVer capture of local schema files: assume SemVer versioning is embedded in root file name 
- Tiny tech debt clean up

## v3.6.0
- Introduced 'critical' category of validation messages (only a handful of messages to start, to be reviewed further)

## v3.5.11
- Bug fix for TRAPI Response sanitization

## v3.5.10
- Extend TRAPI Response sanitization (following Eric Deutsch guidance)

## v3.5.9
- Fixed bug in attribute_type_id detection of attribute_type_id namespaces

## v3.5.8
- implemented get_inverse_predicate() wrapper for returning (CURIE of) valid inverses of predicates (including symmetric predicates?)
- implemented is_symmetric() method to detect symmetric (predicate) elements
- various TRAPI edge case validation against knowledge graph, moved from SRI Testing harness to TRAPIValidator class

## v3.5.7
- patch to fix a previously unnoticed bug in SRI Testing related 'input edge' validation method (wouldn't affect non-SRI Testing related code usage of reasoner-validator)

## v3.5.6
- **ars_uuid_result_test_runner.py**  renamed to **trapi_response_validator.py** and generalized to accept a local TRAPI Response or possibly, an explicit endpoint URL and the TRAPI Request JSON with which to query, whose TRAPI Response is then validated.

## v3.5.5
- Added option to specify 'suppress' as a Biolink Model version string, which triggers suppression of Biolink Model-specific validation of TRAPI JSON messages

## v3.5.4
- Use of a local file path to a TRAPI schema implemented, with code validation using unit tests

## v3.5.3
- fixed query graph validation that was deleting node identifiers in the input query graphs

## v3.5.2 - patched unit test in v3.5.1
- error.trapi.validation 'reason' message text shortened by pruning to use only the start and end of the JSON Schema generated ValidationError message, to a maximum of 160 characters
- unit tests fixed


## v3.5.0
- BMT and related dependencies rehabilitated and simplified? Some BMT functionality removed along the way (hence Minor rather than patch release)

## v3.4.22
- detect all forms of null TRAPI attributes (i.e. strings like "n/a", "none" and "null")
- fixed some technical debt in other pieces of code along the way:
    - Split out the test for an empty message body from the empty response and missing key validation error
    - Query Graphs are allowed to have abstract qualifiers, so the test should not generate an error message
    - 1.4.0-beta4 is the latest TRAPI release
- remove explicit BMT package dependency (rather, expect to to be pulled in by KGX)
- Added deeper validation of RetrievalSource (i.e. checking the resource_id Infores identifiers) plus associated unit tests

## v3.4.21
- pin urllib3  to ^1.26.15 to avoid bug from urllib3 >= 2.0.0
- Update to BMT release v1.0.13 and v2.0.7 for KGX

## v3.4.20
- Shouldn't continue validating an empty TRAPI.Message (and control warnings as indicated)
- Only report qualifier_value misses with Knowledge Graphs (also need to figure out how to avoid these with MetaEdge information)
- Fixed strange reversion of Biolink schema bug to earlier (incorrect) code that was agnostic about 'v' prefix
- Added 'suppress_empty_data_warnings' flag to ars script

## v3.4.19
- special case of biolink:qualified_predicate must have Biolink predicates as values

## v3.4.18
- Added fields specifier to SemVer.from_string() method, to allow lower precision for comparisons of converted SemVer strings (i.e. i.e. major.minor level matches ignoring patch and other suffixes)

## v3.4.17

- Update docs RST to more recent 1.4.0 example code.
- 'suppress_empty_data_warnings' predicate flag added to TRAPIResponseValidator
- Add a SemVer "equal" method override

## v3.4.16

- bug fix relating to incomplete propagation of TRAPI test version to lower code levels where some 1.4.0 features are tested.
- Modest enhancement of Edge.sources validation
- update to BMT 1.0.10

## v3.4.15

- Fixes bug in TRAPI semver which could not process release **`1.4.0-beta2`** because of the missing 'v' prefix.
- Release 1.4.0-beta validation should not now complain about missing Edge attributes
- Significant iteration on repairing unit tests which have differential expectations pre- and post- 1.4.0-beta2 (incomplete?)
- Some basic refactoring starting to fix validation to be 1.4.0-beta (or later) compliant (incomplete)
- TRAPI 'workflow' validation is currently broken due to a [bug in the 1.3.2 Operations Schema]https://github.com/NCATSTranslator/OperationsAndWorkflows/issues/78].
- ValidationReporter.dump(s) 'compress' parameter renamed to 'compact_format' boolean flag

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
