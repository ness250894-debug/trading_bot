import pytest
import sys
import os

if __name__ == "__main__":
    # Add backend to path
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
    
    # Run tests
    print("Running tests...")
    result = pytest.main(['backend/tests/test_full_trading_flow.py', '-v'])
    sys.exit(result)
