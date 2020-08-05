pkgname=qtile-alsavolumecontrol-git
_pkgname=qtile-alsavolumecontrol
pkgver=0.0.1
pkgrel=1
provides=("$_pkgname")
conflicts=("$_pkgname")
pkgdesc="Qtile code to control and display ALSA volume."
url="https://github.com/elparaguayo/qtile-alsavolumecontrol.git"
arch=("any")
license=("MIT")
depends=("python" "qtile")
source=("git+https://github.com/elparaguayo/$_pkgname.git")
md5sums=("SKIP")

pkgver()
{
  cd "$_pkgname"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package()
{
  cd "$_pkgname"
  python setup.py install --root="$pkgdir"
}
