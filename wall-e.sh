#!/bin/bash

cmd=${1}

case $cmd in
run)
    echo "🐔 Running"
    python rpi_thermo_chick/api.py --port 8000
    ;;
wheel)
    echo "🐍 Building wheel ..."
    python setup.py bdist_wheel
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
    python -m twine upload dist/*
    ;;
*)
  echo "Nothing to do ..."
  ;;
esac

echo "💫 Done"