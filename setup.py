#!/usr/bin/env python
"""
Setup script for Customer_Recommender
"""

##########################################################################
## Imports
##########################################################################

try:
    from setuptools import find_packages, setup
    from setuptools.command.install import install as _install 
    from setuptools.command.develop import develop as _develop

except ImportError:
    raise ImportError("Could not import \"setuptools\"."
                      "Please install the setuptools package.")

##########################################################################
## Package Information
##########################################################################

packages = find_packages(where=".", exclude=("tests", "bin", "output",))
requirements = []

with open('requirements.txt', 'r') as reqfile:
    for line in reqfile:
        requirements.append(line.strip())

def _post_install():  
    # since nltk may have just been install
    # we need to update our PYTHONPATH
    import site
    reload(site)
    # Now we can import nltk
    import nltk
    nltk.download('stopwords')

class my_install(_install):  
    def run(self):
        _install.run(self)

        # the second parameter, [], can be replaced with a set of parameters if _post_install needs any
        self.execute(_post_install, [],  
                     msg="Running post install task")


class my_develop(_develop):  
    def run(self):
        self.execute(noop, (self.install_lib,),
                     msg="Running develop task")
        _develop.run(self)
        self.execute(_post_install, [],
                     msg="Running post develop task")

config = {
    "name": "CustomerRecommender",
    "version": "0.1",
    "description": "Recommending the Best Customers for Your Restaurant with Data Science!",
    "author": "Jason Keung",
    "author_email": "jason.s.keung@gmail.com",
    "url": "https://github.com/jkeung/Customer_Recommender",
    "packages": packages,
    # "package_dir": {'': '.'},
    "install_requires": requirements,
    "zip_safe": False,
    "scripts": [],
    "cmdclass":{'install': my_install,  # override install
                'develop': my_develop}  # develop is used for pip install -e .
    }

##########################################################################
## Run setup script
##########################################################################

if __name__ == '__main__':
    setup(**config)