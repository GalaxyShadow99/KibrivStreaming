#!/bin/bash

echo "Installing dependencies from requirements.txt..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Installation failed."
    exit 1
else
    echo "Installation completed successfully."
fi
