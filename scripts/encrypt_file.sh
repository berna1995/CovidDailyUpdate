#!/bin/bash

# Simple script to encrypt files using AES256
# Usage: ./encrypt_secret.sh PASSPHRASE file.txt

gpg --symmetric --batch --yes --cipher-algo AES256 --passphrase="$1" "$2"