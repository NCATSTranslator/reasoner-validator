#!/usr/bin/env python
"""
This super simple script, when run, simply refreshes the cached
local repository copy of the TRAPI releases and branches from GitHub.
This script will typically be run in an appropriate GitAction.
"""
from reasoner_validator.github import get_releases

get_releases(refresh=True)
