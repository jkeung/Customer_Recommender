import os
import requests
from bs4 import BeautifulSoup

def create_dir(directory):

    """Creates directory if doesn't exist

    Args:
        directory: Name of the output directory
    Returns:
        None
    """
    #Check to see if directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_soup_from_url(url):

    """Takes url and returns bs4.BeautifulSoup class.

    Args:
        url (str): A string for the url
    Returns:
        soup (bs4.BeautifulSoup): The beautiful soup object of a given url.

    """    

    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    return soup

