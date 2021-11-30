#!/bin/bash

cmd=${1}

case $cmd in
run)
    echo "🐔 Running"
    python rpi_thermo_chick/api.py --port 8000
wheel)
    echo "🐍 Building wheel ..."
    python setup.py bdist_wheel
    ;;
deploy)
    echo "🚀 Deploying wheel ..."
    #python setup.py bdist_wheel
    ;;
*)
  echo "Nothing to do ..."
  ;;
esac

echo "💫 Done"