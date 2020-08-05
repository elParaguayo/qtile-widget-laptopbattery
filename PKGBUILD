pkgname=qtile-widget-laptopbattery-git
_pkgname=qtile-widget-laptopbattery
pkgver=0.0.1
pkgrel=1
provides=("$_pkgname")
conflicts=("$_pkgname")
pkgdesc="Qtile widget to display laptop battery status."
url="https://github.com/elparaguayo/qtile-widget-laptopbattery.git"
arch=("any")
license=("MIT")
depends=("python" "qtile" "python-pydbus")
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
