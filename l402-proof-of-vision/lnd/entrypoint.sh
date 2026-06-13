#!/bin/sh

set -e

# Wait for bitcoind to be available
echo "Waiting for bitcoind to open RPC port..."
while ! nc -z bitcoind 18443; do
  sleep 1
done
echo "Bitcoind is ready."

# Now execute the main LND command with all arguments passed to the script
exec lnd "$@"
