#!/usr/bin/env python3
"""
Affiliate Bot Startup Script for VPS
Run this script to start the bot in background
"""
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import telegram
        import aiohttp
        import dotenv
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def check_env():
    """Check if .env file exists"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found!")
        print("Copy .env.example to .env and fill in your credentials:")
        print("  cp .env.example .env")
        return False
    
    print("✅ .env file found")
    return True


def start_bot():
    """Start the bot"""
    print("🚀 Starting Affiliate Bot...")
    
    try:
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("  AFFILIATE BOT - Startup Script")
    print("=" * 50)
    print()
    
    # Check prerequisites
    if not check_dependencies():
        sys.exit(1)
    
    if not check_env():
        sys.exit(1)
    
    print()
    start_bot()