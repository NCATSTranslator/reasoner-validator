#!/usr/bin/env python
"""
This super simple executable  script, when run, simply refreshes
the cached local repository copy of the TRAPI releases and branches from GitHub.
This script could typically be run after every new TRAPI release.
"""
from reasoner_validator.github import get_releases

get_releases(refresh=True)
