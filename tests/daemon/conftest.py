"""
Conftest for tests/daemon/.

daemon/__init__.py eagerly imports global_crt which reads POSTGRES_PASSWORD
at module-load. Provide a stub value before pytest collects any test module
here so the imports succeed.
"""
import os
os.environ.setdefault("POSTGRES_PASSWORD", "test_stub")
