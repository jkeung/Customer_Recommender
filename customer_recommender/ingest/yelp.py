#!/usr/bin/env python
import json
import urllib
import urllib2
import os
import time
import pickle
import oauth2
import unicodedata
from pymongo import MongoClient
from ..helper import create_dir, get_soup_from_url
from customer_recommender.config import settings


class Yelp(object):

    OUTPUTDIR = 'output'

    API_HOST = 'api.yelp.com'
    SEARCH_LIMIT = 20
    SEARCH_PATH = '/v2/search/'
    BUSINESS_PATH = '/v2/business/'

    # OAuth credential placeholders that must be filled in by users.
    CONSUMER_KEY = settings.get('consumer_key')
    CONSUMER_SECRET = settings.get('consumer_secret')
    TOKEN = settings.get('access_token')
    TOKEN_SECRET = settings.get('access_token_secret')

    # use exec in order to combine strings from config file with commands
    exec 'DB = MongoClient().{0}'.format(settings.get('database'))
    exec 'COLLECTION = DB.{0}'.format(settings.get('collection'))

    def __init__(self):
        # self.term = raw_input('What food would you like to search for? ')
        self.term = 'restaurants'
        self.location = raw_input('What is your location? ').replace(" ","")
        # self.radius = raw_input('What is your search radius (in meters)? ')
        self.radius = 400

    def request(self, host, path, url_params=None):

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

        consumer = oauth2.Consumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)

        oauth_request.update(
            {
                'oauth_nonce': oauth2.generate_nonce(),
                'oauth_timestamp': oauth2.generate_timestamp(),
                'oauth_token': self.TOKEN,
                'oauth_consumer_key': self.CONSUMER_KEY
            }
        )
        token = oauth2.Token(self.TOKEN,self.TOKEN_SECRET)
        oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
        signed_url = oauth_request.to_url()

        conn = urllib2.urlopen(signed_url, None)
        try:
            response = json.loads(conn.read())
        finally:
            conn.close()

        return response

    def get_business_ids(self, term, location, radius, maxlimit=10000):

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

        # iterate and collect business ids from Yelp
        while resume and offset < 1000:
            url_params = {
                'term': term.replace(' ', '+'),
                'location': location.replace(' ', '+'),
                'limit': 20,
                'radius_filter': radius,
                'offset': offset
            }
            output = self.request(self.API_HOST, self.SEARCH_PATH, url_params = url_params)
            n_records = len(output['businesses'])
            # last set of businesses
            # if n_records < 20:
            #     resume = False
            # only retrieve maxlimit number of reviews or num records < 20
            if offset > maxlimit-20 or n_records < 20:
                resume = False
            # append range of ids to list
            for i in range(n_records):
                # encode to ascii
                business = unicodedata.normalize('NFKD', output['businesses'][i]['id']).encode('ascii','ignore')
                yield business
            # adjust offset
            offset += n_records

    def get_business(self, business_id):

        """Query the Business API by a business ID.

        Args:
            business_id (str): The ID of the business to query.
        Returns:
            dict: The JSON response from the request.
        """

        business_path = self.BUSINESS_PATH + business_id

        return self.request(self.API_HOST, business_path)


    def get_business_url(self, business_id, base = 'http://www.yelp.com/biz/'):

        """Takes business_id and returns the url for a business.

        Args:
            business_id (str): A unique business id for each Yelp business
        Returns:
            business_url (str): The url for the Yelp business.

        """ 

        business_url = base + business_id
        return business_url


    def get_number_reviews(self, business_id):

        """Gets the unique number of reviews for a business.

        Args:
            business_id (str): A unique business id for each Yelp business
        Returns:
            number_reviews (int): The unique number of reviews for a business.
        """ 

        url = self.get_business_url(business_id)
        soup = get_soup_from_url(url)
        number_reviews = int(soup.find(itemprop = 'reviewCount').text)
        return number_reviews


    def get_business_review_info(self, business_id, max_limit = 20):

        """Gets the unique reviews for a business.

        Args:
            business_id (str): A unique business id for each Yelp business
            max_limit (int): Maximum number of requests that can be retrieved
        Returns:
            reviews (list): A list of dictionaries. Each dictionary contains a single review by 
            user containing the date, the review, and the rating.
        """ 

        url = self.get_business_url(business_id)
        new_url = url
        num_reviews = self.get_number_reviews(business_id)
        counter = 0
        reviews = []

        # use a counter to iterate through the url pages
        while counter <= num_reviews:
            soup = get_soup_from_url(new_url)            
            for review in soup.find_all(class_ = 'review--with-sidebar'):
                review_dict = {}
                # get user info
                try:
                    user = review.find(class_ = 'user-display-name').attrs.get('href')
                    review_dict['user'] = user
                except:
                    pass
                # get review
                try:
                    rev = review.find(itemprop='description').text
                    review_dict['review'] = rev
                except:
                    pass
                # get review date
                try:
                    date = review.find(itemprop='datePublished').attrs.get('content')
                    review_dict['date'] = date
                    # review_dict['date'] = datetime.strptime(date,'%Y-%m-%d')
                except:
                    pass
                # get review rating
                try:
                    rating = review.find(itemprop='ratingValue').attrs.get('content')
                    review_dict['rating'] = float(rating)
                except:
                    pass
                # only append if review dict is not empty
                if len(review_dict) != 0:
                    reviews.append(review_dict)
            # increment counter and update url
            counter += max_limit
            new_url = '{0}?start={1}'.format(url, counter)
        return reviews


    def create_business_dictionary(self, business_id):

        """Creates a dictionary for a business with the keys: 'name', 'reviews', 'scores'.

        Args:
            business_id (str): A unique business id for each Yelp business
        Returns:
            d (dict): A dictionary for a given business
        """ 

        # creates outputdir and check to see if output path exists
        outputdir = os.path.join(self.OUTPUTDIR, 'business_dicts')
        create_dir(outputdir)
        output_file = os.path.join(outputdir,'{0}.p'.format(business_id))

        #Check to see if file exists
        try:
            # if exists load from local
            d = pickle.load(open('{0}'.format(output_file), 'rb'))
            print "Loading {0} dictionary from local".format(business_id)
        except:
            # get the data from source
            print ("Processing {0} dictionary...").format(business_id)
            d = {}
            info  = self.get_business(business_id)
            for key, value in info.items():
                d[key] = value
            # overwrites reviews
            d['reviews'] = self.get_business_review_info(business_id)
            d['id'] = business_id
            pickle.dump(d, open('{0}'.format(output_file), 'wb'))
            print (">>> Output saved to {0}").format(output_file)      

    def load_mongodb_data(self, db, collection, business_id):

        """Loads data into a MongoDB

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            business_id (str): A unique business id for each Yelp business
        Returns:
            None
        """ 

        # load from pickle and insert collection into database
        f = os.path.join(self.OUTPUTDIR,'business_dicts','{0}.p'.format(business_id))
        with open(f, 'r') as infile:
            dictionary = pickle.load(infile)
            self.COLLECTION.insert_one(dictionary)

    def main(self):
        start_time = time.time()
        print ("Getting your restaurant reviews...")
        create_dir(self.OUTPUTDIR)

        # clear collection
        print ("Clearing data from MongoDB...")
        self.COLLECTION.drop()

        # scrape and load into MongoDB
        for business_id in self.get_business_ids(self.term, self.location, self.radius):
            print ("Begin {}...".format(business_id))
            self.create_business_dictionary(business_id)
            print ("Loading data into MongoDB...")
            self.load_mongodb_data(self.DB, self.COLLECTION, business_id)
            print ("Loading data into MongoDB complete!")
            print ("Processing {} successful!".format(business_id))

        # time to run
        print ("--- %s seconds ---") % (time.time() - start_time)
        print ("Dictionaries created successfully!")

        
if __name__ == "__main__":
    Yelp().main()
