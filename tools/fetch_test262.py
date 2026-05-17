#!/usr/bin/env python3
from __future__ import annotations

from source_fetching import git_fetch_main


REPO_URL = "https://github.com/tc39/test262.git"
DESTINATION = "external/test262"


if __name__ == "__main__":
    git_fetch_main("test262", REPO_URL, DESTINATION)
