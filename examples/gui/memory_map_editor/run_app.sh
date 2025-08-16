#!/bin/bash
# Memory Map Editor Launcher Script
# This script activates the conda environment and runs the application

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the memory map editor directory
cd "$SCRIPT_DIR"

# Export Qt platform plugin path for conda
export QT_QPA_PLATFORM_PLUGIN_PATH=/Users/bachleviet/opt/anaconda3/plugins/platforms

# Run the application with the conda environment
/Users/bachleviet/opt/anaconda3/bin/conda run -p /Users/bachleviet/opt/anaconda3 python main.py
