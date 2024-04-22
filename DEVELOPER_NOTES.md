# Developer Notes

These notes are only of interest to developers maintaining this repository.

## Maintaining Dependencies

As of release 3.1.6, this project uses the [poetry dependency management](https://python-poetry.org) tool to orchestrate its installation and dependencies. As such, new or revised Python module dependencies are curated within the **pyproject.toml** file.

## Adding or modifying to validation codes

The validation codes are dot-delimited constants represent the hierarchical YAML path in the project's **codes.yaml** file.  The leaves of the YAML paths define the constant into three components:

1. **$message:** the short message description of the meaning of the validation message
2. **$context:** the (YAML) list of parameters which the message may have. The 'identifier' tag generally denotes the TRAPI parse target being parsed. Other tags can provide the validation context such as the identity of the subject-predicate-edge within which the validation issue was encountered.
3. **$description:** a more complete definition of the validation message

After modifying the codes.yaml file, one should run the reasoner_validator.validation_codes.py module as a python script, which regenerates the documentation for new or revised codes in the project's [docs/validation_codes_dictionary.md](docs/validation_codes_dictionary.md) file for revised code.

## TRAPI Version Updates

For Github-related performance reasons, as of project release v3.8.3, the code caches the TRAPI releases and branches from the ReasonerAPI in the **[versions.yaml](reasoner_validator/versions.yaml)** file.  Whenever the TRAPI releases changed significantly, one needs to update this file by running the [scripts/trapi_releases.py](scripts/trapi_releases.py) script, then commit the new **[versions.yaml](reasoner_validator/versions.yaml)** file to Github.

## Project Releases

Steps to properly issue a new project release:

1. Perform any required **codes.yaml** and TRAPI **versions.yaml** updates (as above). 
2. If the **codes.yaml** were revised, regenerated the associate code documentation by running the reasoner_validator/validation_codes.py module as a script from the CLI.
3. Run the unit test suite to ensure that nothing fails. Iterate to fix failures (in the code or in terms of revised unit tests to reflect fresh code designs)
4. Document release changes in the **CHANGELOG.md**
5. Update the **`[Tool Poetry]version =`** field in the **pyprojects.yaml**, e.g. "4.0.2"
6. Run **`poetry update`** (preferably within  **`poetry shell`**)
7. The project pip **requirements.txt** file snapshot of dependencies should also be updated at this point (type **`$ poetry export --output requirements.txt`**, assuming that the [proper poetry export plugin is installed](https://python-poetry.org/docs/pre-commit-hooks#poetry-export)). This may facilitate module deployment within environments that prefer to use pip rather than poetry to manage their deployments. 
8. Commit or pull request merge all files (including the **poetry.lock** file) to **master**
9. Add the equivalent Git **tag** to **master**. This should be the Semantic Version string from step 4 with an added 'v' prefix, i.e. "v4.0.2". 
10. Push **master** to remote.
11. Check if Git Actions for testing and documentation complete successfully.
12. Create the release using the same release tag, i.e. "v4.0.2". 
13. Check if Git Action for package deployment is successful and check if the new version (i.e. "4.0.2") is now visible on **[pypy.org](https://pypi.org/search/?q=reasoner-validator)**
