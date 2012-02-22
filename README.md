# local-repo path [options]

	$ local-repo --help
	usage: local-repo path [options]

	This programm helps to manage local repositories. Specify the path to the
	repository database with the last argument and choose at least one operation
	from the options list.

	positional arguments:
	  path                  path to the repo database

	optional arguments:
	  -h, --help            show this help message and exit
	  -l, --list            list all packages from the repo
	  -i name [name ...], --info name [name ...]
	                        display infos for the specified package
	  -s term, --search term
	                        find packages by term
	  -a path [path ...], --add path [path ...]
	                        add a package to the repo. path can point to a package
	                        file, a pkgbuild tarball or can be the uri of a
	                        downloadable pkgbuild tarball, e.g. in the AUR
	  -u path [path ...], --upgrade path [path ...]
	                        upgrade a package by replacing it with a new package.
	                        see --add for a description of the path argument
	  -r name [name ...], --remove name [name ...]
	                        remove the packages specified by name from the repo
	  -A name [name ...], --aur-add name [name ...]
	                        download, build and add a package specified by name
	                        from the AUR to the repo
	  -U, --aur-upgrade     upgrade all packages in the repo, which are available
	                        in the AUR
	  -c, --check           run an integrity check
	  -R, --restore         Restore repo database
