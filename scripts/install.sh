#!/bin/bash
set -euo pipefail

# Configuration
repo="https://github.com/peerz-ai/peerz.git"
venv_dir="$HOME/.peerz/venv"

# Helper Functions
abort() {
    echo "Error: $@" >&2
    exit 1
}

run_cmd() {
    echo "Executing: $@"
    "$@" || abort "Command failed: $@"
}

install_homebrew() {
    echo "Checking for Homebrew installation..."
    if ! command -v brew &>/dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || abort "Failed to install Homebrew."
    else
        echo "Homebrew is already installed."
    fi
}

setup_python_venv() {
    echo "Setting up Python virtual environment..."
    python3 -m venv "$venv_dir"
    # Activate virtual environment
    source "$venv_dir/bin/activate"
    # Upgrade pip in the virtual environment
    pip install --upgrade pip setuptools wheel
}

install_dependencies() {
    echo "Installing project dependencies in virtual environment..."
    pip install numpy
}

clone_and_setup_peerz() {
    echo "Cloning and setting up peerz..."
    peerz_dir="$HOME/.peerz/peerz"
    mkdir -p "$peerz_dir"
    if [ ! -d "$peerz_dir/.git" ]; then
        run_cmd git clone $repo "$peerz_dir"
    else
        (
            cd "$peerz_dir"
            run_cmd git fetch origin main
            run_cmd git checkout main
            run_cmd git reset --hard origin/main
            run_cmd git clean -xdf
        )
    fi
    pip install -e "$peerz_dir" -v
}

# Main Logic
main() {
    OS="$(uname)"
    if [[ "$OS" == "Darwin" ]]; then
        install_homebrew
    elif [[ "$OS" != "Linux" ]]; then
        abort "This script supports macOS and Linux only."
    fi
    
    setup_python_venv
    install_dependencies
    clone_and_setup_peerz
    echo "peerz setup completed successfully."
    source "$venv_dir/bin/activate"
}

main
