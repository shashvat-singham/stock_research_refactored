import argparse
import os
import subprocess
import sys
import time

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def print_status(message):
    print(f"{BLUE}[INFO]{NC} {message}")


def print_success(message):
    print(f"{GREEN}[SUCCESS]{NC} {message}")


def print_warning(message):
    print(f"{YELLOW}[WARNING]{NC} {message}")


def print_error(message):
    print(f"{RED}[ERROR]{NC} {message}")


def run_command(command, cwd=None, background=False):
    if background:
        return subprocess.Popen(command, shell=True, cwd=cwd)
    else:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
        return None


def start_backend(mode):
    print_status("Starting backend API server...")
    backend_dir = os.getcwd()  # Project root
    # Use same command that works manually
    cmd = "py -m backend.app.main"
    return run_command(cmd, cwd=backend_dir, background=True)


def start_react_frontend(mode):
    print_status("Starting React frontend...")
    frontend_dir = os.path.join(os.getcwd(), "frontend/stock-research-ui")
    if mode == "production":
        run_command("npm run build", cwd=frontend_dir)
        cmd = "npm run preview -- --host 0.0.0.0 --port 3000"
    else:
        cmd = "npm run dev -- --host 0.0.0.0 --port 3000"
    return run_command(cmd, cwd=frontend_dir, background=True)


def start_streamlit_frontend():
    print_status("Starting Streamlit frontend...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    cmd = "py -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
    return run_command(cmd, cwd=frontend_dir, background=True)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")  # Ensure we are in the project root

    parser = argparse.ArgumentParser(description="Start the Stock Research Chatbot application.")
    parser.add_argument("--mode", type=str, default="development", choices=["development", "production"],
                        help="Set mode (development|production) [default: development]")
    parser.add_argument("--frontend", type=str, default="react", choices=["react", "streamlit", "both"],
                        help="Set frontend (react|streamlit|both) [default: react]")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies before starting")
    args = parser.parse_args()

    print_status("Starting Stock Research Chatbot...")
    print_status(f"Mode: {args.mode}")
    print_status(f"Frontend: {args.frontend}")

    # Check if .env file exists
    if not os.path.isfile(".env"):
        print_error(".env file not found!")
        print_status("Creating .env file from template...")
        if os.path.isfile(".env.template"):
            run_command("cp .env.template .env")
            print_warning("Please edit .env file with your API keys before running again")
            sys.exit(1)
        else:
            print_error(".env.template file not found!")
            sys.exit(1)

    # Install dependencies if requested
    if args.install_deps:
        print_status("Installing Python dependencies...")
        run_command("pip install -r backend/requirements.txt")

        if args.frontend == "react" or args.frontend == "both":
            print_status("Installing Node.js dependencies...")
            run_command("npm install --legacy-peer-deps", cwd="frontend/stock-research-ui")

    processes = []

    if args.mode == "development":
        if args.frontend == "react" or args.frontend == "both":
            processes.append(start_backend(args.mode))
            time.sleep(3)  # Give backend time to start
            processes.append(start_react_frontend(args.mode))
        elif args.frontend == "streamlit":
            processes.append(start_backend(args.mode))
            time.sleep(3)
            processes.append(start_streamlit_frontend())

        if args.frontend == "both":
            processes.append(start_streamlit_frontend())

    elif args.mode == "production":
        processes.append(start_backend(args.mode))

    print_success("All services started!")
    print_status("Backend API: http://localhost:8000")
    if args.frontend == "react" or args.frontend == "both":
        print_status("React Frontend: http://localhost:3000")
    if args.frontend == "streamlit" or args.frontend == "both":
        print_status("Streamlit Frontend: http://localhost:8501")
    print_status("API Documentation: http://localhost:8000/docs")

    try:
        for p in processes:
            if p:
                p.wait()
    except KeyboardInterrupt:
        print_warning("Shutting down services...")
        for p in processes:
            if p and p.poll() is None:
                p.terminate()
        for p in processes:
            if p:
                p.wait()
        print_success("Services shut down.")


if __name__ == "__main__":
    main()
