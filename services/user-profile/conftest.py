"""Ensure the service src directory is on the Python path for tests."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
