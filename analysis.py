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


db = MongoClient().yelpdb
collection = db.review_collection
stop = stopwords.words('english')


def preprocess_review(review, term):
    """ Takes a review and preprocesses the review for sentiment analysis by keeping only
    the reviews that relate to the search term, making all the words lowercase, removing punctuation, 
    and tokenizing the sentence."""
    
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
    d = defaultdict(int)
    cursor = collection.find({"$and": [ 
                                {"review": {"$regex": term}}, 
                                {"name": restaurant} 
                                ]
    })    
    for i in cursor:
        if cursor.count() > min_reviews:
            # preprocess the reviews
            review = preprocess_review(i['review'], term)

            # add sentiment score and review count to the dictionary
            d['scores'] += TextBlob(review).sentiment[0]
            d['reviews'] += 1
    if d['reviews'] > 0:
        d['avg_scores'] = d['scores'] / d['reviews']
    else:
        d['avg_scores'] = 0
    return d['avg_scores']

def get_trending_words(db, collection, term, restaurant, ngram = 2, num_words = 5):
    words_dict = defaultdict(int)
    top_words_list = []

    cursor = collection.find({"$and": [ 
                                {"review": {"$regex": term}}, 
                                {"name": restaurant} 
                                ]
    })    
    for i in cursor:
        # preprocess the reviews
        review = preprocess_review(i['review'], term)

        # track words that appear often and filter out stopwords
        words = wordpunct_tokenize(review)
        words = [w for w in words if w not in stop]
        # words = [word for word, pos in pos_tag(words) if pos in ['JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS'] and word not in stop]
           
        # get bigrams and store in dictionary
        for i in range(ngram):
            n_gram = ngrams(words, i+1)
            for gram in n_gram:
                words_dict[gram] += 1  
            
        top_words_list = get_top_n_trending_phrases(words_dict, num_words)
    return top_words_list

def get_top_n_restaurants(avg_scores_dict, n):
    d = {}
    for restaurant, score in sorted(avg_scores_dict.items(), key=itemgetter(1), reverse = True):
        d[restaurant] = score
    return d

def get_top_n_trending_phrases(words_dict, n):
    l = []
    for phrase, count in sorted(words_dict.items(), key=itemgetter(1), reverse = True)[:n]:
        l.append(" ".join(phrase))
    return l

def get_json(db, collection, term, n_grams, num_restaurants, num_reviews, num_words):
    restaurants = collection.distinct("name")

    list_of_restaurant_dicts = []

    for restaurant in restaurants:
        output = {}
        output['name'] = restaurant
        output['score'] = get_average_scores(db, collection, term, restaurant)
        output['words'] =  get_trending_words(db, collection, term, restaurant)
        list_of_restaurant_dicts.append(output)

    return list_of_restaurant_dicts

def main():
    n_grams = 1
    term = 'pizza'
    num_restaurants = 10
    num_reviews = 5
    num_words = 10
    d = get_json(db, collection, term, n_grams, num_restaurants, num_reviews, num_words)
    return d

if __name__ == '__main__':
    main()