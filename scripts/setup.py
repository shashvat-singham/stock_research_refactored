
import os
import subprocess
import sys

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m' # No Color

def print_status(message):
    print(f"{BLUE}[INFO]{NC} {message}")

def print_success(message):
    print(f"{GREEN}[SUCCESS]{NC} {message}")

def print_warning(message):
    print(f"{YELLOW}[WARNING]{NC} {message}")

def print_error(message):
    print(f"{RED}[ERROR]{NC} {message}")

def run_command(command, cwd=None, check=True):
    try:
        subprocess.run(command, shell=True, check=check, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}\n{e}")
        sys.exit(1)

def setup_environment():
    print_status("Setting up Stock Research Chatbot development environment...")

    # Check Python version
    print_status("Checking Python version...")
    if sys.version_info < (3, 11):
        print_error(f"Python 3.11+ is required, found {sys.version.split()[0]}")
        sys.exit(1)
    print_success(f"Python {sys.version.split()[0]} is compatible")

    # Check Node.js version
    print_status("Checking Node.js version...")
    try:
        subprocess.run("node --version", shell=True, check=True, capture_output=True)
        print_success("Node.js found")
    except subprocess.CalledProcessError:
        print_error("Node.js is required but not installed")
        sys.exit(1)

    # Create virtual environment if it doesn't exist
    if not os.path.isdir("venv"):
        print_status("Creating Python virtual environment...")
        run_command("py -m venv venv")
        print_success("Virtual environment created")
    else:
        print_status("Virtual environment already exists")

    # Activate virtual environment (Note: This needs to be done manually in the terminal or handled by the calling script)
    print_status("Please activate the virtual environment manually: `venv\Scripts\Activate.ps1 `")

    # Install Python dependencies
    print_status("Installing Python dependencies...")
    run_command("py -m pip install --upgrade pip")
    run_command("py -m pip install -r backend/requirements.txt")
    print_success("Python dependencies installed")

    # Install Node.js dependencies for React frontend
    if os.path.isdir("frontend/stock-research-ui"):
        print_status("Installing Node.js dependencies for React frontend...")
        run_command("npm install --legacy-peer-deps", cwd="frontend/stock-research-ui")
        print_success("React frontend dependencies installed")

    # Install Streamlit dependencies
    print_status("Installing Streamlit dependencies...")
    run_command("pip install streamlit plotly")
    print_success("Streamlit dependencies installed")

    # Create .env file if it doesn't exist
    if not os.path.isfile(".env"):
        print_status("Creating .env file from template...")
        if os.path.isfile(".env.template"):
            run_command("cp .env.template .env")
            print_warning("Please edit .env file with your API keys")
        else:
            print_error(".env.template file not found!")
            sys.exit(1)
    else:
        print_status(".env file already exists")

    # Create data directories
    print_status("Creating data directories...")
    os.makedirs("data/chroma_db", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print_success("Data directories created")

    # Run tests to verify setup
    print_status("Running tests to verify setup...")
    if subprocess.run("python -m pytest backend/tests/ -v --tb=short", shell=True, check=False).returncode == 0:
        print_success("All tests passed!")
    else:
        print_warning("Some tests failed, but setup is complete")

    print_success("Development environment setup complete!")
    print_status("\nNext steps:")
    print_status("1. Edit .env file with your API keys")
    print_status("2. Activate the virtual environment: `source venv/bin/activate` (Linux/macOS) or `.\venv\Scripts\activate` (Windows)")
    print_status("3. Run `python scripts/start.py` to start the application")
    print_status("4. Visit http://localhost:8000/docs for API documentation")
    print_status("5. Visit http://localhost:3000 for React frontend")
    print_status("6. Visit http://localhost:8501 for Streamlit frontend") 

if __name__ == "__main__":
    # os.chdir('/home/ubuntu/stock-research-chatbot') # Ensure we are in the project root
    setup_environment()

