import sys
import os

print("Python path:", sys.path)
print("Current directory:", os.getcwd())

# Try to import our modules
sys.path.insert(0, os.path.abspath('python_backend'))
print("After adding python_backend to path, trying imports...")

try:
    from hyba_genesis_api.api.misc import PredictRequest, predict_params
    print("✓ Imported PredictRequest and predict_params")
except Exception as e:
    print(f"✗ Failed to import: {e}")

try:
    from pythia_mining.genesis_ai_service import GenesisAIServiceRegistry
    print("✓ Imported GenesisAIServiceRegistry")
except Exception as e:
    print(f"✗ Failed to import: {e}")

print("All checks complete!")
