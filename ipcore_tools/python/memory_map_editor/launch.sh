#!/bin/bash
# Launcher script that properly activates the conda environment

echo "Memory Map Editor Launcher"
echo "=========================="

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda not found. Please install Anaconda/Miniconda."
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Activating conda base environment..."

# Source conda and activate base environment
source /Users/bachleviet/opt/anaconda3/etc/profile.d/conda.sh
conda activate base

echo "Checking dependencies..."

# Check if required packages are installed
python -c "import PySide6; print('✓ PySide6 available')" || {
    echo "Installing PySide6..."
    pip install PySide6
}

python -c "import yaml; print('✓ PyYAML available')" || {
    echo "Installing PyYAML..."
    pip install PyYAML
}

echo "Starting Memory Map Editor..."
cd "$SCRIPT_DIR"

# Try to fix Qt platform plugin path issues
export QT_QPA_PLATFORM_PLUGIN_PATH="/Users/bachleviet/opt/anaconda3/plugins/platforms"

# Alternative: use XQuartz if available (for X11 forwarding)
if command -v xquartz &> /dev/null; then
    export DISPLAY=:0
fi

# Run the application
echo "Running: python main.py $@"
python main.py "$@"

# If it fails due to Qt issues, provide helpful message
if [ $? -ne 0 ]; then
    echo ""
    echo "If you're seeing Qt platform plugin errors, try:"
    echo "1. Running from VS Code with the Python extension"
    echo "2. Or run: conda install qt -c conda-forge"
    echo "3. Or try: export QT_QPA_PLATFORM=offscreen && python main.py"
fi
