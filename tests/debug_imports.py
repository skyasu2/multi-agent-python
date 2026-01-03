
import sys
import os

# Project Root Setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Project Path: {project_root}")

print("-" * 20)
print("1. Testing utils.schemas import...")
try:
    import utils.schemas
    print("utils.schemas imported successfully.")
    print(f"DraftResult in dir: {'DraftResult' in dir(utils.schemas)}")
except Exception as e:
    print(f"FAIL: {e}")

print("-" * 20)
print("2. Testing graph.state import...")
try:
    import graph.state
    print("graph.state imported successfully.")
except Exception as e:
    print(f"FAIL: {e}")

print("-" * 20)
print("3. Testing agents.writer import...")
try:
    import agents.writer
    print("agents.writer imported imported successfully.")
except Exception as e:
    print(f"FAIL: {e}")
