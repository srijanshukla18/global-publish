#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the main python script with all arguments passed to this script
python main.py "$@"
