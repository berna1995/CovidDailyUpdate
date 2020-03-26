#!/bin/bash

dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
cd $dir
cd ..

pkill -F proc.pid &> /dev/null

set -e

pipenv install --deploy
nohup pipenv run python src/main.py &> logs.log &
echo $! > proc.pid
