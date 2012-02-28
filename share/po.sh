#!/bin/sh

usage() {
	echo "usage: ${0} template|merge|compile"
	echo ''
	echo 'template  creates a po template from the source files'
	echo 'merge     merges an updated template in to existing po files'
	echo 'compile   compiles the po files'
}

if [ $# -ne 1 ]; then
	usage
	exit 1
fi

cd $(dirname "$0")

case "$1" in
	template)
		echo -e '\e[1;33mGenerating:\e[0m messages.pot'
		xgettext -o - -L Python ../local-repo ../localrepo/*.py |\
			sed 's/\(charset=\)CHARSET/\1UTF-8/' |\
			sed 's/SOME DESCRIPTIVE TITLE\./local-repo translation file/' |\
			sed 's/\(Copyright (C)\).\+/\1 2012 ushi/' |\
			sed 's/\(same license as the\) PACKAGE/\1 local-repo/' |\
			sed 's/\(Project-Id-Version:\) PACKAGE VERSION/\1 1.4/' > messages.pot
		;;
	merge)
		if [ ! -f messages.pot ]; then
			echo -e '\e[1;31mNothing to merge:\e[0m messages.pot does not exist'
			exit 1
		fi
		if [ ! -d translations ]; then
			echo -e '\e[1;31mNothing to merge:\e[0m translations/ does not exist'
			exit 1
		fi
		for f in $(ls translations/*.po); do
			echo -e "\e[1;33mUpdating:\e[0m ${f}"
			msgmerge -UNq --backup=off "$f" messages.pot
		done
		;;
	compile)
		if [ ! -d translations ]; then
			echo -e '\e[1;31mNothing to compile:\e[0m translations/ does not exist'
			exit 1
		fi
		for f in $(ls translations/*.po); do
			echo -e "\e[1;33mCompiling:\e[0m ${f}"
			lang=$(basename "$f" | cut -d'.' -f1)
			dir="locale/${lang}/LC_MESSAGES"
			[[ ! -d "$dir" ]] && mkdir -p "$dir"
			msgfmt "$f" -o "${dir}/localrepo.mo"
		done
		;;
	*)
		usage
		exit 1
		;;
esac
