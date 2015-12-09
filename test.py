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
import pandas as pd
import collections
import unicodedata


db = MongoClient().yelpdb
collection = db.review_collection
collection2 = db.score_collection
stop = stopwords.words('english')

df = pd.DataFrame(columns = ['date', 'rating', 'review', 'user'])
cursor = collection.find()
for i in cursor:
#     new_df = pd.DataFrame(i['reviews'])
    df = df.append(pd.DataFrame(i['reviews']))

print df.groupby('user').agg({'review': 'count', 'rating':'mean'}).sort('review', ascending = False)