#!/bin/bash

cmd=${1}

case $cmd in
run)
    echo "🐔 Running"
    python3 rpi_thermo_chick/api.py --port 8000
    ;;
wheel)
    echo "🐍 Building wheel ..."
    pip install wheel
    rm -r $(pwd)/dist
    python3 setup.py bdist_wheel
    ;;
clean)
    echo "🧨 Cleaning wheel ..."
    rm -r $(pwd)/__pycache__
    rm -r $(pwd)/dist
    rm -r $(pwd)/build
    rm -r $(pwd)/rpi_thermo_chick.egg-info
    ;;  
deploy)
    echo "🚀 Deploying wheel ..."
    pip install twine
    python3 -m twine upload dist/*
    ;;
bootstrap)
    echo "🚀 Bootstrap dev ..."
    python3 -m venv _env
    source _env/bin/activate
    pip install wheel
    pip install -e .
    ;;
*)
  echo "Nothing to do ..."
  ;;
esac

echo "💫 Done"