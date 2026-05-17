#!/usr/bin/env python3
from __future__ import annotations

from source_fetching import git_fetch_main


REPO_URL = "https://github.com/json-schema-org/JSON-Schema-Test-Suite.git"
DESTINATION = "external/json-schema-test-suite"


if __name__ == "__main__":
    git_fetch_main("json_schema_test_suite", REPO_URL, DESTINATION)
