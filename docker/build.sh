#!/usr/bin/env bash

# move to FFmpeg root dir
cd "$(dirname "${BASH_SOURCE[0]}")" && cd ..

# Build(+push?) Docker image
python -m docker.build "$@"
