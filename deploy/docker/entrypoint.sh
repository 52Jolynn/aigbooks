#!/bin/sh
set -e

nginx -t
nginx

exec "$@"