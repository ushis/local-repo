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
		xgettext -o - -L Python ../local-repo ../localrepo/*.py |\
			sed 's/charset=CHARSET/charset=UTF-8/' > messages.po
		echo -e '\e[1;33mGenerated:\e[0m messages.po '
		;;
	merge)
		if [ ! -f messages.po ]; then
			echo -e '\e[1;31mNothing to merge:\e[0m messages.po does not exist'
			exit 1
		fi
		if [ ! -d translations ]; then
			echo -e '\e[1;31mNothing to merge:\e[0m translations/ does not exist'
			exit 1
		fi
		for f in $(ls translations/*.po); do
			msgmerge -UNq --backup=off "$f" messages.po
			echo -e "\e[1;33mUpdated:\e[0m ${f}"
		done
		;;
	compile)
		if [ ! -d translations ]; then
			echo -e '\e[1;31mNothing to compile:\e[0m translations/ does not exist'
			exit 1
		fi
		for f in $(ls translations/*.po); do
			lang=$(basename "$f" | cut -d'.' -f1)
			dir="locale/${lang}/LC_MESSAGES"
			[[ ! -d "$dir" ]] && mkdir -p "$dir"
			msgfmt "$f" -o "${dir}/localrepo.mo"
			echo -e "\e[1;33mCompiled:\e[0m ${dir}/localrepo.mo"
		done
		;;
	*)
		usage
		exit 1
		;;
esac
