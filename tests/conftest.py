"""Shared pytest fixtures and environment setup.

Forces APP_ENV=development for the test process so that ApplicationConfig
does not require a WF_SECRET_KEY (production/test mode) when individual
service or repository constructors instantiate it transitively. Tests that
need to exercise production-mode behaviour patch os.environ explicitly.
"""

import os

os.environ.setdefault("APP_ENV", "development")
