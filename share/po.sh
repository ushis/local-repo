#!/bin/sh

usage() {
	echo "usage: ${0} t|template|m|merge|c|compile"
	echo ''
	echo 't, template  creates a po template from the source files'
	echo 'm, merge     merges an updated template in to existing po files'
	echo '             Note: There is no real need for this anymore. Just'
	echo '                   push the new pot file to the devel branch,'
	echo '                   Transifex will take care of the rest.'
	echo 'c, compile   compiles the po files'
}

if [ $# -ne 1 ]; then
	usage
	exit 1
fi

cd $(dirname "$0")

POT=messages.pot
ARGPARSE=argparse.pot
TRANS=translations
MO=localrepo.mo

case "$1" in
	t|template)
		echo -e "\e[1;33mGenerating:\e[0m ${POT}"
		xgettext -o - -L Python ../local-repo ../localrepo/*.py |\
			sed 's/\(charset=\)CHARSET/\1UTF-8/' |\
			sed 's/SOME DESCRIPTIVE TITLE\./local-repo translation file/' |\
			sed 's/\(Copyright (C)\).\+/\1 2012 ushi/' |\
			sed 's/\(same license as the\) PACKAGE/\1 local-repo/' |\
			sed 's/\(Project-Id-Version:\) PACKAGE VERSION/\1 local-repo 1.6/' > "$POT"

		if [ -f "$ARGPARSE" ]; then
			echo '' >> "$POT"
			cat "$ARGPARSE" >> "$POT"
		fi
		;;
	m|merge)
		if [ ! -f "$POT" ]; then
			echo -e "\e[1;31mNothing to merge:\e[0m ${POT} does not exist"
			exit 1
		fi
		if [ ! -d "$TRANS" ]; then
			echo -e "\e[1;31mNothing to merge:\e[0m ${TRANS}/ does not exist"
			exit 1
		fi
		for f in $(ls $TRANS/*.po); do
			echo -e "\e[1;33mUpdating:\e[0m ${f}"
			msgmerge -UNq --backup=off "$f" "$POT"
		done
		;;
	c|compile)
		if [ ! -d "$TRANS" ]; then
			echo -e "\e[1;31mNothing to compile:\e[0m ${TRANS} does not exist"
			exit 1
		fi
		for f in $(ls $TRANS/*.po); do
			echo -e "\e[1;33mCompiling:\e[0m ${f}"
			lang=$(basename "$f" | cut -d'.' -f1)
			dir="locale/${lang}/LC_MESSAGES"
			[[ ! -d "$dir" ]] && mkdir -p "$dir"
			msgfmt "$f" -o "${dir}/${MO}"
		done
		;;
	*)
		usage
		exit 1
		;;
esac
