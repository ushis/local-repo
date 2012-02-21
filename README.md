# local-repo [options] path

	usage: local-repo [options] path

	This programm helps to manage local repositories. Specify the path to the
	repository database with the last argument and choose at least one operation
	from the options list.

	positional arguments:
	  path                  path to the repo database

	optional arguments:
	  -h, --help            show this help message and exit
	  -l, --list            list all packages from the repo
	  -i name, --info name  display infos for the specified package
	  -s term, --search term
	                        find packages by term
	  -a path, --add path   add a package to the repo. path can point to a package
	                        file, a pkgbuild tarball or can be the uri of a
	                        downloadable pkgbuild tarball, e.g. in the AUR
	  -u path, --upgrade path
	                        upgrade a package by replacing it with a new package.
	                        see --add for a description of the path argument
	  -r name, --remove name
	                        remove the package specified by name from the repo
	  -A name, --aur-add name
	                        download, build and add a package specified by name
	                        from the AUR to the repo
	  -U, --aur-upgrade     upgrade all packages in the repo, which are available
	                        in the AUR
	  -c, --check           run an integrity check
	  -R, --restore         Restore repo database
