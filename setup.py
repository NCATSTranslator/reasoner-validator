from setuptools import setup

def read_production_requirements():
    # read requirements from requirements.txt
    prod_dependency_links = []
    prod_requirements = []
    with open('requirements.txt') as f:
        parsed_requirements_file = f.read().splitlines()
        # iterate through the file
        for requirement in parsed_requirements_file:
            # parse out index urls
            if requirement.startswith("-i"):
                prod_dependency_links.append(requirement)
            # ignore commands and whitespace
            elif not requirement.startswith('#') or not requirement.strip() == '':
                prod_requirements.append(requirement)
    return prod_requirements, prod_dependency_links

def read_dev_requirements():
    # read requirements from requirements.txt
    dev_dependency_links = []
    dev_requirements = []
    with open('requirements-dev.txt') as f:
        parsed_requirements_file = f.read().splitlines()
        # iterate through the file
        for requirement in parsed_requirements_file:
            # parse out index urls
            if requirement.startswith("-i"):
                dev_dependency_links.append(requirement)
            # ignore commands and whitespace
            elif not requirement.startswith('#') or not requirement.strip() == '':
                dev_requirements.append(requirement)
    return dev_requirements, dev_dependency_links

prod_requirements, prod_dependency_links = read_production_requirements()
# dev_requirements, dev_dependency_links = read_dev_requirements()
# perform setup

setup(
    install_requires=prod_requirements,
    dependency_links=prod_dependency_links
)