#!/bin/bash

# This script links the system-wide SoapySDR Python module and its C extension
# into the local uv virtual environment.

set -e

# Find the system-level SoapySDR installation
SOAPY_SDR_PY=$(python3 -c "import SoapySDR; print(SoapySDR.__file__)")
SOAPY_SDR_SO="/usr/local/lib/python3.11/dist-packages/_SoapySDR.so"

if [ -z "$SOAPY_SDR_PY" ]; then
    echo "Error: System-wide SoapySDR.py module not found."
    exit 1
fi

if [ ! -f "$SOAPY_SDR_SO" ]; then
    echo "Error: System-wide _SoapySDR.so module not found at $SOAPY_SDR_SO"
    exit 1
fi

# Identify the Python version used within the virtual environment
VENV_PYTHON_VERSION=$(./.venv/bin/python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")

VENV_SITE_PACKAGES=".venv/lib/python${VENV_PYTHON_VERSION}/site-packages/"

# Ensure the site-packages directory exists
mkdir -p "$VENV_SITE_PACKAGES"

# Create symbolic links to both the Python wrapper and C extension
ln -sf "$SOAPY_SDR_PY" "$VENV_SITE_PACKAGES"
ln -sf "$SOAPY_SDR_SO" "$VENV_SITE_PACKAGES"

echo "Successfully created symbolic links for SoapySDR.py and _SoapySDR.so in the virtual environment." 