#!/bin/sh

cd $(dirname "$0")

# YEAH! Test them all..
for f in *.py; do
	echo ''
	echo "Testing $f"
	echo '----------------------------------------------------------------------'
	python -S "$f" || exit 1
done
