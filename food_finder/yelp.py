#!/usr/bin/env python
import json
import urllib
import urllib2
import cnfg
import os
import time
import pickle
import requests
import oauth2
from bs4 import BeautifulSoup
from pymongo import MongoClient
import unicodedata
# import socks
# import socket


# socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5, addr="127.0.0.1", port=9050)
# socket.socket = socks.socksocket

print requests.get("http://icanhazip.com").text
print requests.get("http://www.yelp.com/biz/99-cent-express-pizza-new-york").text
config = cnfg.load(".yelp/.yelp_config")

OUTPUTDIR = 'output'

# DEFAULT_TERM = 'pizza'
# DEFAULT_LOCATION = 'New York, NY'
# DEFAULT_RADIUS = 2000

API_HOST = 'api.yelp.com'
SEARCH_LIMIT = 20
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

# OAuth credential placeholders that must be filled in by users.
CONSUMER_KEY = config["consumer_key"]
CONSUMER_SECRET = config["consumer_secret"]
TOKEN = config["access_token"]
TOKEN_SECRET = config["access_token_secret"]

client = MongoClient()
db = MongoClient().yelpdb
collection = db.review_collection

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

def get_business_ids(term, location, radius, maxlimit=20):

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

def get_business(business_id):

    """Query the Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """

    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path)

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

def get_business_url(business_id, base = 'http://www.yelp.com/biz/'):

    """Takes business_id and returns the url for a business.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        business_url (str): The url for the Yelp business.

    """ 

    business_url = base + business_id
    return business_url

def get_number_reviews(business_id):

    """Gets the unique number of reviews for a business.

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

    """Gets all of customer reviews for a business.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        reviews (list): All the reviews for a given business.
    """ 

    reviews = []
    counter = 0
    url = get_business_url(business_id)
    new_url = url
    num_reviews = get_number_reviews(business_id)
    
    while counter <= num_reviews:
        soup = get_soup_from_url(new_url)
        review_list = soup.find(class_ = 'review-list')
        for review in review_list.find_all(itemprop='description'):
            reviews.append(review.text)
        counter += max_limit
        new_url = '{0}?start={1}'.format(url, counter)
    return reviews

def get_all_scores_for_business(business_id, max_limit = 20):

    """Gets all of customer review scores for a business.

    Args:
        business_id (str): A unique business id for each Yelp business
    Returns:
        scores (list): All the review scores for a given business.
    """ 

    scores = []
    counter = 0
    url = get_business_url(business_id)
    new_url = url
    num_reviews = get_number_reviews(business_id)
    
    while counter <= num_reviews:
        soup = get_soup_from_url(new_url)
        review_list = soup.find(class_ = 'review-list')
        for score in review_list.find_all(class_ = 'rating-very-large'):
            try:
                rating = float(score.find(itemprop = 'ratingValue')['content'][0])
                scores.append(rating)
            except:
                pass
        counter += max_limit
        new_url = '{0}?start={1}'.format(url, counter)
    return scores

def create_business_dictionary(business_id, outputdir):

    """Creates a dictionary for a business with the keys: 'name', 'reviews', 'scores'.

    Args:
        business_id (str): A unique business id for each Yelp business
        outputdir (str): A specified path for where the output should be created
    Returns:
        d (dict): A dictionary for a given business
    """ 

    # creates outputdir and check to see if output path exists
    create_dir(outputdir)
    output_file = os.path.join(outputdir, '{0}.p'.format(business_id))

    #Check to see if file exists
    try:
        # if exists load from loacl
        d = pickle.load(open('{}'.format(output_file), 'rb'))
        print "Loading {} dictionary from local".format(business_id)
    except:
        # get the data from source
        print ("Processing {0} dictionary...").format(business_id)
        d = {}
        info  = get_business(business_id)
        for key, value in info.items():
            d[key] = value
        # overwrites reviews
        d['reviews'] = get_all_reviews_for_business(business_id)
        d['sentiment_scores'] = get_all_scores_for_business(business_id)
        d['id'] = business_id

        pickle.dump(d, open('{}'.format(output_file), 'wb'))
        print (">>> Output saved to {0}").format(output_file)   
    return d    

def load_mongodb_data(db, collection, business_ids):
    
    """Loads data into a MongoDB

    Args:
        db (str): MongoDB database name
        collection (str): MongoDB collection name
        term (str): Search term
        location (str): Search location
        radius (int): Search radius
    Returns:
        None
    """ 

    collection.drop()

    for business_id in business_ids:
        business_id = unicodedata.normalize('NFKD', business_id).encode('ascii','ignore')
        f = os.path.join(OUTPUTDIR,'{0}.p'.format(business_id))
        with open(f, 'r') as infile:
            dictionary = pickle.load(infile)
            collection.insert_one(dictionary)

def main():

    start_time = time.time()
    term = raw_input('What food would you like to search for? ')
    location = raw_input('What is your location? ')
    radius = raw_input('What is your search radius (in meters)? ')

    # term = DEFAULT_TERM
    # location = DEFAULT_LOCATION
    # radius = DEFAULT_RADIUS

    location = location.replace(" ","")
    print ("Getting your restaurant reviews...")
    business_ids = get_business_ids(term, location, radius)
    for business_id in business_ids:
        business_id = unicodedata.normalize('NFKD', business_id).encode('ascii','ignore')
        outputdir = os.path.join(OUTPUTDIR)
        create_business_dictionary(business_id, outputdir)
    print ("--- %s seconds ---") % (time.time() - start_time)
    print ("Dictionaries created successfully!")

    print ("Loading data into MongoDB...")
    load_mongodb_data(db, collection, business_ids)
    print ("Loading data into MongoDB complete!")

if __name__ == '__main__':
    main()