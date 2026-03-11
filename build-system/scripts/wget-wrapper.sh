#!/bin/bash
# wget wrapper - silently handles Contents-amd64.gz 404 errors
REAL_WGET=/usr/bin/wget
for arg in "$@"; do
  if [[ "$arg" == *"Contents"* ]]; then
    exit 0
  fi
done
exec "$REAL_WGET" "$@"
