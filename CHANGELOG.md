# Change Log

The Reasoner Validator package is evolving along with progress in TRAPI and Biolink standards within the NCATS Biomedical Knowledge Translator. 

## 1.* releases

Preliminary releases of the validation code, now obsolete.

## 2.* releases

Had a simple base TRAPI schema 'validate' with errors throwing a Python exception; later minor iterations added in Biolink Model validation returning a flat dictionary of arcane string messages.

## 3.* releases

Wrapped the all validation with a ValidatorReporter class serving to collect and return validation messages in a disciplined, codified manner (as a [master YAML file with hierarchically-indexed Python string templates](reasoner_validator/codes.yaml))

## Recent Change Log

### 3.1.6

- Some structural changes to project (Sphinx) documentation
- Added markdown generator for reading codes.yaml as a Markdown document in the project documentation.
- Created this formal change log!

