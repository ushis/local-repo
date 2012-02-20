# Maintainer: ushi <ushi@porkbox.net>
pkgname=local-repo
pkgver=1.0
pkgrel=1
pkgdesc="Local repository manager"
arch=('any')
url="https://github.com/ushis/local-repo"
license=('GPL')
depends=('wget' 'tar' 'pacman' 'python')
makedepends=()
source=($pkgname-$pkgver.tar.gz)
md5sums=()

package() {
  cd "$srcdir/$pkgname-$pkgver"
  make DESTDIR="$pkgdir/" install
}

# vim:set ts=2 sw=2 et:
