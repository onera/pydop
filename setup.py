import glob
import os
import sys
from setuptools import setup

name = "pydop"
description = "Python package for the creation of delta-oriented Software Product Lines."
authors = {
    "gzoumix": ("Michael Lienhardt", "michael.lienhardt@onera.fr",),
}
maintainer = "Michael Lienhardt"
maintainer_email = "michael.lienhardt@onera.fr"
url = None
project_urls = {
    "Bug Tracker": None,
    "Documentation": None,
    "Source Code": None,
}
platforms = ["Linux", "Mac OSX", "Windows", "Unix"]
keywords = [
    "Software Product Lines",
    "Multi-Software Product Lines",
    "Delta-Oriented Programming",
    "Variability",
    "Software Engineering",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Code Generators",
]

with open("pydop/__init__.py") as fid:
    for line in fid:
        if line.startswith("__version__"):
            version = line.strip().split()[-1][1:-1]
            break

packages = glob.glob("pydop/*.py") + glob.glob("pydop/operations/*.py")



install_requires = []
extras_require = ["networkx>=3.0"]

if __name__ == "__main__":
    setup(
        name=name,
        version=version,
        maintainer=maintainer,
        maintainer_email=maintainer_email,
        author=authors["gzoumix"][0],
        author_email=authors["gzoumix"][1],
        description=description,
        keywords=keywords,
        long_description=description,
        platforms=platforms,
        url=url,
        project_urls=project_urls,
        classifiers=classifiers,
        packages=packages,
        install_requires=install_requires,
        extras_require=extras_require,
        python_requires=">=3",
        zip_safe=False,
    )

