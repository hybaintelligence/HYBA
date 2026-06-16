import sys
import os

# Add the project root and python_backend to the Python path
sys.path.insert(0, os.path.abspath('/Users/demouser/Desktop/HYBA_FULLSTACK'))
sys.path.insert(0, os.path.abspath('/Users/demouser/Desktop/HYBA_FULLSTACK/python_backend'))

import unittest

# Discover and run the tests
loader = unittest.TestLoader()
suite = loader.discover('tests', pattern='test_prediction_endpoint.py')
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with non-zero code if there were failures or errors
if result.failures or result.errors:
    sys.exit(1)
else:
    sys.exit(0)
