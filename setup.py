from setuptools import setup

setup(
    name='qtile-widget-laptopbattery',
    packages=['laptopbattery'],
    version='0.1.0',
    description='A qtile widget to show laptop battery status.',
    author='elParaguayo',
    url='https://github.com/elparaguayo/qtile-widget-laptopbattery',
    license='MIT',
    install_requires=['qtile>0.14.2', 'pydbus']
)
