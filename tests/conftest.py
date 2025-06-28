import sys
import os

# Add project root directory to sys.path
# This allows tests to import modules from the 'app' directory as 'app.xxx'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
