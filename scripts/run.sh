#!/bin/bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
cd $dir
cd ..

pkill -F proc.pid &> /dev/null

set -e

poetry install --no-root --no-dev
nohup poetry run python -m bot &> logs.log &
echo $! > proc.pid
