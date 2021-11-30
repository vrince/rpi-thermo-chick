#!/bin/bash

cmd=${1}

case $cmd in
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