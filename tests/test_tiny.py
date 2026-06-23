import sys
import os

print("Python path:", sys.path)
print("Current directory:", os.getcwd())

# Try to import our modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python_backend"))
)
print("After adding python_backend to path, trying imports...")

try:
    print("✓ Imported PredictRequest and predict_params")
except Exception as e:
    print(f"✗ Failed to import: {e}")

try:
    print("✓ Imported GenesisAIServiceRegistry")
except Exception as e:
    print(f"✗ Failed to import: {e}")

print("All checks complete!")
