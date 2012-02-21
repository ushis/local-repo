# Maintainer: ushi <ushi@porkbox.net>
pkgname=local-repo
pkgver=1.1
pkgrel=1
pkgdesc="Local repository manager"
arch=('any')
url="https://github.com/ushis/local-repo"
license=('GPL')
depends=('tar' 'pacman' 'python')
makedepends=()
source=("https://github.com/downloads/ushis/local-repo/local-repo-${pkgver}.tar.gz")
md5sums=('149849df5eb3ff539e371c31c345f0fc')

package() {
  cd "${srcdir}/${pkgname}"
  python setup.py install --prefix="${pkgdir}/usr"
}

# vim:set ts=2 sw=2 et:
