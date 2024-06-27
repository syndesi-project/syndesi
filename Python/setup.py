from setuptools import setup, find_packages

VERSION = '0.2.1'
DESCRIPTION = 'Syndesi'

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Setting up
setup(
    name="syndesi",
    version=VERSION,
    author="Sebastien Deriaz",
    author_email="sebastien.deriaz1@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    entry_points = {
        'console_scripts': [
            'syndesi=syndesi.shell.syndesi:main',
            'syndesi-proxy=syndesi.proxy.proxy:main'],
    },
    packages=find_packages(),
    install_requires=[''],
    keywords=['python', 'syndesi', 'interface', 'ethernet'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows"
    ]
)
