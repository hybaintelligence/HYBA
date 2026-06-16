import sys
import os

# Add the project root and python_backend to the Python path
sys.path.insert(0, os.path.abspath('/Users/demouser/Desktop/HYBA_FULLSTACK'))
sys.path.insert(0, os.path.abspath('/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend'))

import pytest

# Run the test
pytest.main([
    'tests/test_prediction_endpoint.py',
    '-v',
    '--tb=short'
])
