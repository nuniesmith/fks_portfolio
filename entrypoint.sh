#!/bin/bash
set -e

echo "FKS Portfolio Platform - Starting..."

# Run the CLI with provided arguments or default
exec python src/cli.py "$@"

