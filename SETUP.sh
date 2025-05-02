#!/bin/bash

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

# Function to setup venv
setup_venv() {
    # Check if venv exists
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment '$VENV_DIR' already exists."
    else
        echo "Creating virtual environment '$VENV_DIR'..."
        python3 -m venv "$VENV_DIR"
        echo "✅ Virtual environment created."
    fi

    # Install requirements if file exists
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo "Installing dependencies from $REQUIREMENTS_FILE..."
        source "$VENV_DIR/bin/activate"
        pip install -r "$REQUIREMENTS_FILE"
        deactivate  # Deactivate after install
        echo "✅ Dependencies installed."
    else
        echo "No $REQUIREMENTS_FILE found. Skipping dependency installation."
    fi

    # Print activation instructions
    echo ""
    echo "Virtual environment is ready! To activate it, run:"
    echo "source $VENV_DIR/bin/activate"
}

# Run setup
setup_venv