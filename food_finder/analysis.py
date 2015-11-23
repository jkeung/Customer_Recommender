#!/usr/bin/env python
from nltk.tokenize import sent_tokenize
from nltk.tokenize import wordpunct_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.util import ngrams
import string
import re
from pymongo import MongoClient
from collections import defaultdict
from textblob import TextBlob
from operator import itemgetter
from pprint import pprint
import collections


db = MongoClient().yelpdb
collection = db.review_collection
collection2 = db.score_collection
stop = stopwords.words('english')

def preprocess_review(review, term):
    """ Takes a review and preprocesses the review for sentiment analysis by keeping only
    the reviews that relate to the search term, making all the words lowercase, removing punctuation, 
    and tokenizing the sentence.

    Args:
        review (str): A user's review
        term (str): Search term
    Returns:
        review (str): A cleaned review

    """
    
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    
    # tokenize and make sentences lowercase
    sentences = sent_tokenize(review.lower())
    
    # only keep sentences that relate to the specific food search term
    filtered_sentences = filter(lambda x: term in x, sentences)

    # recreate review without punctuation
    sentence = "".join(filtered_sentences) 
    cleaned_review = regex.sub('',sentence)

    return cleaned_review


def get_average_scores(db, collection, term, restaurant, min_reviews = 5):

    """Calculates the average score for a restaurant and stores 'sentiment_scores' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            term (str): Search term
            restaurant (str): Restaurant's id
            min_reviews (int): Minimum number of reviews for the score to be calculated
        Returns:
            review (str): A cleaned review
    """

    d = defaultdict(int)
    cursor = collection.find({"id": restaurant})  
    reviews = cursor.next()['reviews']
    for review in reviews:
        if len(reviews) > min_reviews:
            # preprocess the reviews
            rev = preprocess_review(review, term)

            # add sentiment score and review count to the dictionary
            d['sentiment_scores'] += TextBlob(rev).sentiment[0]
            d['reviews'] += 1
        break
    if d['reviews'] > 0:
        d['avg_scores'] = d['sentiment_scores'] / d['reviews']
    else:
        d['avg_scores'] = 0.0
    return d['avg_scores']


def get_trending_words(db, collection, term, restaurant, ngram = 2, num_words = 5):

    """Calculates the average score for a restaurant and stores 'sentiment_scores' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            term (str): Search term
            restaurant (str): Restaurant's id
            ngram (int): Types of ngrams to go up to
            num_words (int): Number of top words to return
        Returns:
            top_words_list (list): List of top words that appear
    """

    words_dict = defaultdict(int)
    top_words_list = []

    cursor = collection.find({"id": restaurant})  
    reviews = cursor.next()['reviews']
    for review in reviews:  
        # preprocess the reviews
        rev = preprocess_review(review, term)

        # track words that appear often and filter out stopwords
        words = wordpunct_tokenize(rev)
        words = [w for w in words if w not in stop]
        # words = [word for word, pos in pos_tag(words) if pos in ['JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS'] and word not in stop]

        # get bigrams and store in dictionary
        for i in range(ngram):
            n_gram = ngrams(words, 1)
            for gram in n_gram:
                words_dict[gram] += 1  
        
        top_words_list = get_top_n_trending_phrases(words_dict, num_words)
    return top_words_list


def get_restaurant_name(db, collection, restaurant):

    """Retrieve restaurant name and stores 'name' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            restaurant (str): Restaurant's id
        Returns:
            name (str): List of top words that appear
    """

    cursor = collection.find({"id": restaurant})  
    name = cursor.next()['name']
    return name


def get_restaurant_rating(db, collection, restaurant):

    """Retrieve restaurant name and stores 'rating' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            restaurant (str): Restaurant's id
        Returns:
            rating (float): Restaurant user rating
    """
    cursor = collection.find({"id": restaurant})  
    rating = cursor.next()['rating']
    return rating


def get_restaurant_image(db, collection, restaurant):

    """Retrieve restaurant name and stores 'image' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            restaurant (str): Restaurant's id
        Returns:
            image (str): Link for the restaurant user review image
    """

    cursor = collection.find({"id": restaurant})  
    image = cursor.next()['rating_img_url_small']
    return image


def get_restaurant_location_coordinates(db, collection, restaurant):

    """Retrieve restaurant name and stores 'name' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            restaurant (str): Restaurant's id
        Returns:
            coordinate (dict): Dictionary of latitude and longitude coordinates
    """
    
    cursor = collection.find({"id": restaurant}) 
    try: 
        coordinate = cursor.next()['location']['coordinate']
    except:
        coordinate = {'latitude': 0, 'longitude': 0}
    return coordinate


def get_restaurant_neighborhood(db, collection, restaurant):

    """Retrieve restaurant name and stores 'neighborhood' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            restaurant (str): Restaurant's id
        Returns:
            neighborhood (str): Restaurant neighborhood
    """

    cursor = collection.find({"id": restaurant})  
    try:
        neighborhood = cursor.next()['location']['neighborhoods']
    except:
        neighborhood = 'Not Listed'
    return neighborhood


def get_top_n_trending_phrases(words_dict, n):

    """Retrieve restaurant name and stores 'name' into the MongoDB collection.

        Args:
            words_dict (dict): dictionary of words that appear in reviews
            n (int): number of words to be returned
        Returns:
            l (list): list of top trending phrases
    """

    l = []
    for phrase, count in sorted(words_dict.items(), key=itemgetter(1), reverse = True)[:n]:
        l.append(" ".join(phrase))
    return l


def get_json(db, collection, term):

    """Retrieve restaurant name and stores 'name' into the MongoDB collection.

        Args:
            db (str): MongoDB database name
            collection (str): MongoDB collection name
            term (str): Search term
        Returns:
            output_list (list): List of restaurant dictionaries
    """

    restaurants = collection.distinct('id')

    # list_of_restaurant_dicts = []
    output = {}
    output_list = []

    # get the name, scores, and top words for restaurants and reviews
    for restaurant in restaurants:
        print "Processing {0}".format(restaurant)
        output[restaurant] = {}
        output[restaurant]['name'] = get_restaurant_name(db, collection, restaurant)
        output[restaurant]['id'] = restaurant
        output[restaurant]['sentiment_scores'] = get_average_scores(db, collection, term, restaurant)
        output[restaurant]['words'] =  get_trending_words(db, collection, term, restaurant)
        output[restaurant]['rating'] =  get_restaurant_rating(db, collection, restaurant)
        output[restaurant]['image'] = get_restaurant_image(db, collection, restaurant)
        output[restaurant]['coordinate'] = get_restaurant_location_coordinates(db, collection, restaurant)
        output[restaurant]['neighborhood'] = get_restaurant_neighborhood(db, collection, restaurant)

    # rank restaurants by scores, descending
    ranked_restaurants = sorted([restaurant for restaurant in restaurants], key=lambda x: (output[x]['sentiment_scores']), reverse = True)
    
    # create the list of dictionaries to output
    for restaurant in ranked_restaurants:
        output_list.append(output[restaurant])

    return output_list[:10]


def main():
    n_grams = 1
    term = 'pizza'
    num_restaurants = 10
    num_reviews = 5
    num_words = 10
    print ("Getting list of dictionaries...")
    lst = get_json(db, collection, term)
    print ("Clearning MongoDB Collection...")
    collection2.drop()
    print ("Loading MongoDB Collection...")
    for restaurant in lst:
        collection2.insert_one(restaurant)
    print ("Loading MongoDB Collection complete!")


if __name__ == '__main__':
    main()