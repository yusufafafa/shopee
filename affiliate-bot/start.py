"""Quick start script for Affiliate Bot"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import main

if __name__ == "__main__":
    print("🚀 Starting Affiliate Bot...")
    print("Press Ctrl+C to stop\n")
    main()