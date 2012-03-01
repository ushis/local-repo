# local-repo path [options]

	$ local-repo --help
	usage: local-repo path [options]

	This programm helps to manage local repositories. Specify the path to the
	repository with the first argument. If no option is specified, some repo
	informations will be printed.

	positional arguments:
	  path                  path to the repo

	optional arguments:
	  -h, --help            show this help message and exit
	  -a path [path ...], --add path [path ...]
	                        add a package to the repo. path can point to a package
	                        file, a pkgbuild tarball or can be the uri of a
	                        downloadable pkgbuild tarball, e.g. in the AUR
	  -A name [name ...], --aur-add name [name ...]
	                        download, build and add a package specified by name
	                        from the AUR to the repo
	  -c, --check           run an integrity check
	  -e, --elephant        the elephant never forgets
	  -i name [name ...], --info name [name ...]
	                        display infos for the specified package
	  -l, --list            list all packages from the repo
	  -r name [name ...], --remove name [name ...]
	                        remove the packages specified by name from the repo
	  -R, --restore         Restore repo database
	  -s term, --search term
	                        find packages by term
	  -u path [path ...], --upgrade path [path ...]
	                        upgrade a package by replacing it with a new package.
	                        see --add for a description of the path argument
	  -U, --aur-upgrade     upgrade all packages in the repo, which are available
	                        in the AUR
	  -V, --vcs-upgrade     upgrade all packages in the repo, which are based on a
	                        VCS and available in the AUR

# Examples

## Creating a new repo

One way of creating a repo is to create an empty diretory and add some packages, eg from the AUR
using -A.

	$ mkdir /tmp/repo
	$ local-repo /tmp/repo -A package1 package2 package3

If you already have some packages in a directory, you can use the -R option

	$ cd /path/to/packages
	$ ls
	package1.pkg.tar.xz
	package2.pkg.tar.xz
	package3.pkg.tar.xz
	$ local-repo ./ -R

# Translators

I am very happy about any contribution. The easiest way to contribute is to add a translation.

## How?

Go to https://www.transifex.net/projects/p/local-repo/ and translate into your preferred language.
Its that easy.

## Dont like Transifex?

This is a little bit more complicated, but no problem for experienced git users.

1. Fork local-repo and clone it
1. Check out the devel branch

	```
	$ cd /path/to/local-repo
	$ git checkout devel
	```

1. Check if your language already exists. ```mylang``` is something like 'en' or 'de'

	```
	$ cd share
	$ ls translations/ | grep mylang
	```

1. Copy the template into the translations folder. Replace ```mylang``` by your language.
   **If your language already exists, you should skip this.**

	```
	$ cp messages.pot translations/mylang.po
	```

1. Edit the language file.
1. If you want to test your translation (This would be very nice!), compile the language files
   and launch the programm. *You need to have installed the gettext package for doin this.*

	```
	$ ./po.sh compile
	$ ../local-repo path [options]
	```
1. Add, commit and push your changes and send me a pull request. Choose 'devel' as integration
   branch.

Happy translating!

# LICENSE

	Copyright (c) 2012 ushi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
