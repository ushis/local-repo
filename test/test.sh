#!/bin/sh

# YEAH! Test them all..
for f in *.py; do
	echo ''
	echo "Testing $f"
	echo '----------------------------------------------------------------------'
	python -S "$f"
done
