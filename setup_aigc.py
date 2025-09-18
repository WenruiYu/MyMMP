#!/usr/bin/env python3
"""
AIGC Setup Script for MoneyPrinterPlus
Ensures proper installation and configuration for different PCs
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required for AIGC functionality")
        return False
    
    print("✅ Python version is compatible")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    # Core dependencies for AIGC
    core_deps = [
        "openai>=1.40.0",
        "python-dotenv",
        "streamlit>=1.34.0",
        "pathlib",
        "pyyaml",
        "requests"
    ]
    
    for dep in core_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True

def setup_environment():
    """Setup environment variables."""
    print("🔧 Setting up environment variables...")
    
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print(f"📝 Creating .env file from template...")
        import shutil
        shutil.copy(env_example, env_file)
        print(f"✅ .env file created at {env_file}")
        print("⚠️  Please edit .env file and add your API keys!")
    elif env_file.exists():
        print(f"✅ .env file already exists at {env_file}")
    else:
        print("⚠️  No .env template found. Please create .env file manually.")
    
    # Check if DEEPSEEK_API_KEY is set
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key and deepseek_key != "your_deepseek_api_key_here":
        print("✅ DEEPSEEK_API_KEY is configured")
        return True
    else:
        print("⚠️  DEEPSEEK_API_KEY not configured in .env file")
        return False

def test_aigc_import():
    """Test if AIGC services can be imported."""
    print("🧪 Testing AIGC service imports...")
    
    try:
        # Test core imports
        from pathlib import Path
        import yaml
        print("✅ Core dependencies imported successfully")
        
        # Test AIGC service
        sys.path.insert(0, str(Path(__file__).parent / "MoneyPrinterPlus-windows"))
        from services.aigc.aigc_service import AIGCService
        print("✅ AIGC service imported successfully")
        
        # Test rewriter core
        sys.path.insert(0, str(Path(__file__).parent / "aigc"))
        from rewriter_core import RewriterConfig
        print("✅ Rewriter core imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main setup process."""
    print("🚀 AIGC Setup for MoneyPrinterPlus")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Setup failed: Incompatible Python version")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Dependency installation failed")
        return False
    
    # Setup environment
    env_configured = setup_environment()
    
    # Test imports
    if not test_aigc_import():
        print("\n❌ Setup failed: Import test failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 AIGC Setup Completed Successfully!")
    print("\n📋 Next Steps:")
    
    if not env_configured:
        print("1. ⚠️  Edit .env file and add your DEEPSEEK_API_KEY")
        print("2. 🚀 Start MoneyPrinterPlus: streamlit run MoneyPrinterPlus-windows/main.py")
        print("3. 📝 Navigate to 'AI Content Rewriter' page")
    else:
        print("1. 🚀 Start MoneyPrinterPlus: streamlit run MoneyPrinterPlus-windows/main.py")
        print("2. 📝 Navigate to 'AI Content Rewriter' page")
        print("3. 🎯 Start generating content!")
    
    print("\n💡 If you encounter OpenAI client errors:")
    print("   Run: pip install --upgrade openai>=1.35.0")
    print("   Remove conflicting packages: pip uninstall langchain langchain-openai langchain-community")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
