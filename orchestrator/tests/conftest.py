"""
INDUSTRIAL ORCHESTRATOR TEST CONFIGURATION
Pytest configuration and fixtures for all tests.
"""

import sys
from pathlib import Path

# Add orchestrator root directory (parent of src) to Python path for imports
# This allows imports like: from src.industrial_orchestrator...
orchestrator_root = Path(__file__).parent.parent
if str(orchestrator_root) not in sys.path:
    sys.path.insert(0, str(orchestrator_root))

