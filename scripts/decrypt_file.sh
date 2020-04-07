#!/bin/bash

# Simple script to decrypt a file

# Set an environment variable called DECRYPT_PASSPHRASE containing passphrase before running
# Usage: ./decrypt_secret.sh outputfile.txt inputfile.gpg

gpg --batch --yes --decrypt --passphrase="$DECRYPT_PASSPHRASE" --output="$1" $2