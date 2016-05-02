#!/usr/bin/env python3.4

from setuptools import setup, find_packages

def install():
    return setup(name = "kooc",
                 version = "0.1",
                 install_requires=["pyrser", "sphinx", "cnorm"]
    )

if __name__ == "__main__":
    install()
    print("\n\n\
    !----------------------------------------------!\n\n\
    In order for everything to run smoothly, set your path like :\n\
    export PYTHONPATH=$PYTHONPATH:/PATH/TO/KOOC/sources\n\
    and :\n\
    export KOOCPATH=:/PATH/TO/KOOC/.conf\n\n\
    !----------------------------------------------!\n")
