# Customer Recommender Overview

An app that scrapes all the restaurants within a 1000m radius and will help you find the 'best' customers for your restaurant in your neighborhood!

## Clone the repository

```$ git clone https://github.com/jkeung/Customer_Recommender.git
```

## Setup

This code is portable across the following OS's: Linux distributions, Mac and Windows OS's. Scripts were written using Python 2.7 and have not been tested for portability to Python 3.X.

You are encouraged to use a python virtual environment using virtualenv and pip. 

```$ virtualenv venv
```

### Install requirements:

```$ pip install -r requirements.txt
```

#### Description of modules imported and application

* beautifulsoup4 - Beautiful Soup sits atop an HTML or XML parser, providing Pythonic idioms for iterating, searching, and modifying the parse tree.
* Flask - Flask is a microframework for Python based on Werkzeug, Jinja 2 and good intentions.
* httplib2 - A comprehensive HTTP client library, httplib2 supports many features left out of other HTTP libraries.
* itsdangerous - Various helpers to pass trusted data to untrusted environments and back
* Jinja2 - Jinja2 is a full featured template engine for Python. It has full unicode support, an optional integrated sandboxed execution environment, widely used and BSD licensed
* lxml - The lxml XML toolkit is a Pythonic binding for the C libraries libxml2 and libxslt. It is unique in that it combines the speed and XML feature completeness of these libraries with the simplicity of a native Python API
* MarkupSafe - Implements a XML/HTML/XHTML Markup safe string for Python
* nltk - NLTK is a leading platform for building Python programs to work with human language data
* numpy - NumPy is the fundamental package for scientific computing with Python
* oauth2 - python-oauth2 is a framework that aims at making it easy to provide authentication via OAuth 2.0 within an application stack
* pandas - pandas is an open source, BSD-licensed library providing high-performance, easy-to-use data structures and data analysis tools for the Python programming language
* pymongo - Python driver for MongoDB
* python-dateutil - Extensions to the standard Python datetime module
* pytz - World timezone definitions, modern and historical
* PyYAML - A YAML parser and emitter for Python
* requests - An Apache2 Licensed HTTP library, written in Python, for human beings
* scikit-learn - Machine Learning in Python
* scipy - A Python-based ecosystem of open-source software for mathematics, science, and engineering
* six - Python 2 and 3 compatibility utilities
* Werkzeug - Werkzeug is a WSGI utility library for Python
* wheel - A built-package format for Python

If there are issues install lxml on Mac OSX, libxml2 and libxslt may be required. (http://stackoverflow.com/questions/19548011/cannot-install-lxml-on-mac-os-x-10-9)

```
brew install libxml2
brew install libxslt
brew link libxml2 --force
brew link libxslt --force
```

## Set up MongoDB (skip this step if MongoDB is already installed)

Follow instructions found here to install and setup MongoDB:
	
```
https://docs.mongodb.org/manual/installation/
```

Ensure that the MongoDB daemon is running by running: 
```$ mongod
```

## Install NLTK dependencies:

```$ python -m nltk.downloader all
```

## Set your Yelp API Credentials

In the 'conf' folder rename the template.yaml file to config.yaml and configure the settings. A Yelp API key can be obtained here: https://www.yelp.com/developers

## Run Scraping and Analyzing Script

Application can be run separately or all at once from a shell script.

#### To run separately:

```
$ python -m customer_recommender.ingest.yelp

$ python -m customer_recommender.wrangle.cluster_data

$ python customer_recommender/visualize/app.py 
```

#### To run via shell script:

```$ source bin/customer_recommender.sh
```


## Run Flask App!

The Flask app should be visible at the following location: 

```
http://127.0.0.1:5000/
```

