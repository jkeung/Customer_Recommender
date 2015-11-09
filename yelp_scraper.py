import argparse
import json
import pprint
import sys
import urllib
import urllib2
import cnfg
import urlparse
import os
import time
import pickle
import requests
import oauth2
from bs4 import BeautifulSoup
from sys import argv

config = cnfg.load(".yelp/.yelp_config")

OUTPUTDIR = 'output'
FILENAMETEMPLATE = 'business_dicts'

API_HOST = 'api.yelp.com'
DEFAULT_TERM = 'pizza'
DEFAULT_LOCATION = 'New York, NY'
DEFAULT_RADIUS = 200
SEARCH_LIMIT = 20
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

# OAuth credential placeholders that must be filled in by users.
CONSUMER_KEY = config["consumer_key"]
CONSUMER_SECRET = config["consumer_secret"]
TOKEN = config["access_token"]
TOKEN_SECRET = config["access_token_secret"]

def request(host, path, url_params=None):

    """Prepares OAuth authentication and sends the request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'https://{0}{1}?'.format(host, urllib.quote(path.encode('utf8')))

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': TOKEN,
            'oauth_consumer_key': CONSUMER_KEY
        }
    )
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response

def get_business_ids(term = DEFAULT_TERM, location = DEFAULT_LOCATION, radius = DEFAULT_RADIUS, maxlimit=20):

    """Function to get the business_ids from the yelp API.

    Args:
        term (str): The search term.
        location (str): The location to search for.
        radius (int): The radius (in meters) for the search.
        maxlimit (int): An optional set of query parameters in the request for maximim results returned. (Max is 20)
    Returns:
        businesses (list): A list of all the business_ids for the search.

    """

    offset = 0
    businesses = []
    resume = True
    while resume:
        url_params = {
            'term': term.replace(' ', '+'),
            'location': location.replace(' ', '+'),
            'limit': maxlimit,
            'radius_filter': radius,
            'offset': offset
        }
        output = request(API_HOST, SEARCH_PATH, url_params = url_params)
        n_records = len(output['businesses'])
        if n_records < 20:
            resume = False
        for i in range(n_records):
            businesses.append(output['businesses'][i]['id']) 
        offset += n_records
    return businesses

def create_dir(directory):
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

def get_business_url(business_id, base = 'http://www.yelp.com/biz/'):

    """ Takes business_id and returns the url for a business.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        business_url (str): The url for the Yelp business.

    """ 

    business_url = base + business_id
    return business_url

def get_number_reviews(business_id):

    """ Gets the unique number of reviews for a business.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        number_reviews (int): The unique number of reviews for a business.
    """ 

    url = get_business_url(business_id)
    soup = get_soup_from_url(url)
    number_reviews = int(soup.find(itemprop = 'reviewCount').text)
    return number_reviews

def get_all_reviews_for_business(business_id, max_limit = 20):

    """ Get all the reviews for a business.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        reviews (list): A list of all the reviews reviews for a business.
    """ 

    reviews = []
    counter = 0
    url = get_business_url(business_id)
    new_url = url
    num_reviews = get_number_reviews(business_id)
    
    while counter <= num_reviews:
        soup = get_soup_from_url(new_url)
        for elem in soup.find(class_ = 'review-list').find_all(itemprop='description'):
            reviews.append(elem.text)
        counter += max_limit
        new_url = '{}?start={}'.format(url, counter)
    return reviews

def make_business_reviews_dict(business_ids):

    """ Creates a dictionary that using the business_id as a key and a list of the reviews as a value.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        d (dict): A dictionary that has the business_id as a key and a list of the reviews as a value.
    """ 

    d = {}
    for business_id in business_ids:
        d[business_id] = get_all_reviews_for_business(business_id)
    return d

def main():

    start_time = time.time()
    term = raw_input('What food would you like to search for? ')
    location = raw_input('What is your location? ')
    radius = raw_input('What is your search radius (in meters)? ')
    print ("Getting your restaurant reviews...")
    business_ids = get_business_ids(term, location, radius)

    create_dir(OUTPUTDIR)
    output_path = os.path.join(OUTPUTDIR, '{0}_{1}_{2}_{3}.p'.format(FILENAMETEMPLATE, term, location, radius))

    d = make_business_reviews_dict(business_ids)
    pickle.dump(d, open('{}'.format(output_path.replace(' ','')), 'wb'))

    print ("--- %s seconds ---") % (time.time() - start_time)
    print ("Dictionary created successfully!")
    print ("Output saved to {0}").format(output_path)

if __name__ == '__main__':
    main()