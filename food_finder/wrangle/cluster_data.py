from pymongo import MongoClient

import pandas as pd
import nltk
import re
import os
import random

from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import wordpunct_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

DB = MongoClient().yelpdb
COLLECTION = DB.review_collection


def get_top_users(df, min_reviews=5):
    """Function to get the top users from the cleaned dataframe.

    Args:
        df (pandas.DataFrame): The dataframe containing all the reviews, ratings, dates, restaurant, and users
        min_reviews (int): The minimum number of reviews a user must have to be considered a top_user
    Returns:
        top_users (list): A list of the top local Yelp reviewers

    """
    top_users_df = df.groupby('user').agg({'review': 'count'}).sort_values(by='review', ascending = False)
    top_users = top_users_df[top_users_df['review']>min_reviews].index.tolist()
    return top_users


def tokenize_and_stem(text, stemmer=SnowballStemmer("english")):
    """Word and sentence tokenization function that utilizes the Snowball Stemmer

    Args:
        text (string): All the reviews for a single user concatenated into a single string
        stemmer (Stemmer): The stemmer to be used
    Returns:
        stems (list): The filtered and stemmed tokens

    """
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in wordpunct_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems


def tokenize_only(text):
    """Word and sentence tokenization function without stemming

    Args:
        text (string): All the reviews for a single user concatenated into a single string
    Returns:
        filtered_tokens (list): The filtered tokens

    """
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in wordpunct_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    return filtered_tokens


def get_raw_dataframe(collection):
    """Function to get raw data from MongoDB collection

    Args:
        collection (string): MongoDB collection
    Returns:
        df (pandas.DataFrame): Raw dataframe data

    """

    df = pd.DataFrame()
    cursor = collection.find()
    for i in cursor:
        new_df = pd.DataFrame(i['reviews'])
        new_df['restaurant'] = i['id']
        df = df.append(new_df)
    return df


def create_user_df(df):
    """Function to create a DataFrame grouped by user. The review column contains all the reviews for a specific 
       user as a string.

    Args:
        collection (string): MongoDB collection
    Returns:
        df (pandas.DataFrame): DataFrame with users and reviews

    """

    user_review_list = []
    for user in get_top_users(df):
        d = {}
        reviews = ''
        df2 = df[df['user']==user]
        for review in df2['review'].tolist():
            reviews += review
        d['user'] = user
        d['reviews'] = reviews
        user_review_list.append(d)
    return pd.DataFrame(user_review_list)


def get_stop_words(stop):
    """Function to append a custom list of stop words to the nltk.stopwords.

    Args:
        stop (list): List of stopwords
    Returns:
        stop (list): List of stopwords

    """
    stop.extend(["don't", "don", "didn't", "should've", "could've", "would've", "m", "got", "get", "came", "pretty", "ve"])
    return stop


def build_vocab_frame(reviews, stop):
    """Function to build a vocabulary frame with stemmed words and original words

    Args:
        reviews (list): List of reviews
        stop (list): List of stopwords
    Returns:
        vocab_frame (pandas.DataFrame): Data frame with stemmed words and original words

    """

    totalvocab_stemmed = []
    totalvocab_tokenized = []

    for review_corpus in reviews:
        allwords_stemmed = tokenize_and_stem(review_corpus)
        totalvocab_stemmed.extend(allwords_stemmed)

        allwords_tokenized = tokenize_only(review_corpus)
        totalvocab_tokenized.extend(allwords_tokenized)
        vocab_frame = pd.DataFrame({'words': totalvocab_tokenized}, index=totalvocab_stemmed)
    return vocab_frame


def get_cluster_words_dict(reviews, vocab_frame, km, num_clusters, terms):
    """Function to obtain the top words for each cluster. 

    Args:
        reviews (list): List of reviews
        vocab_frame (pandas.DataFrame): Data frame with stemmed words and original words
        km (KMeans): K means model
        num_clusters: Number of clusters
        terms (list): List of words found in clusters
    Returns:
        cluster_words_dict (dict): A dictionary of cluster number and closest cluster words

    """

    clusters = km.labels_.tolist()
    # sort cluster centers by proximity to centroid
    order_centroids = km.cluster_centers_.argsort()[:, ::-1] 

    cluster_words_dict = {}
    for i in range(num_clusters):
        word_list = []
        num_words = 5
        cluster_words_dict[i] = ' '.join([vocab_frame.ix[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore') \
                                          for ind in order_centroids[i, :5]])
    return cluster_words_dict


def manually_define_clusters():
    """Function to manually label clusters. This should be run after clusters have been identified.

    Args:
        None
    Returns:
        cluster_words_dict (dict): A dictionary of cluster number and closest cluster words

    """

    # Do manual check to make sense of the clusters
    cluster_words_dict = {
        0:"Happy Hours",
        1:"Burgers and Shakes",
        2:"Lunch Sandwiches, Salads, and Soups",
        3:"Indian Food",
        4:"Sit Down Lunch",
        5:"Korean Food",
        6:"Wines and Brunch",
        7:"Spicy Rice Dishes",
        8:"Desserts",
        9:"Pizza Lovers"
    }
    return cluster_words_dict


def clean_df(df, cluster_words_dict, km, users):
    """Function to create final cleaned dataframe for analysis. 

    Args:
        df (pandas.DataFrame): Raw dataframe data
        cluster_words_dict (dict): A dictionary of cluster number and closest cluster words
        km (KMeans): K means model
        users (list): List of users
    Returns:
        cluster_words_dict (dict): A dictionary of cluster number and closest cluster words

    """

    filtered_df = df.groupby('user').agg({'rating':'mean','review':'count','date':'max'}).sort_values(by='review', ascending = False)
    filtered_df = filtered_df[filtered_df['review']>5]
    final_df = filtered_df.join(pd.DataFrame(km.labels_.tolist(), index = [users] , columns = ['cluster']), how = 'inner')
    final_df = final_df.sort_values(by=['cluster','rating','review'], ascending = [True,False,False])
    final_df.reset_index(inplace = True)
    final_df.rename(columns = {'review':'num_reviews'}, inplace = True)
    final_df.rename(columns = {'rating':'avg_rating'}, inplace = True)
    final_df.rename(columns = {'date':'last_review_date'}, inplace = True)
    final_df.rename(columns = {'index':'user'}, inplace = True)
    final_df['cluster_name'] = final_df['cluster'].apply(lambda x: cluster_words_dict[x])
    final_df['cluster'] = final_df['cluster'].apply(lambda x: x + 1)
    final_df['avg_rating'] = final_df['avg_rating'].apply(lambda x: round(float(x),2))
    final_df['user'] = final_df['user'].apply(lambda x:'www.yelp.com' + x)
    return final_df


def main():

    random.seed(2)
    stop = get_stop_words(stopwords.words('english'))
    df = get_raw_dataframe(COLLECTION)
    user_df = create_user_df(df)

    users = user_df['user'].tolist()
    reviews = user_df['reviews'].tolist()

    vocab_frame = build_vocab_frame(reviews, stop)
    tfidf_vectorizer = TfidfVectorizer(max_df=0.8, 
                                       max_features=200000,
                                       min_df=0.2, 
                                       lowercase=True,
                                       stop_words=stop,
                                       use_idf=True, 
                                       tokenizer=tokenize_and_stem, 
                                       ngram_range=(1,3))

    tfidf_matrix = tfidf_vectorizer.fit_transform(reviews) #fit the vectorizer to reviews
    terms = tfidf_vectorizer.get_feature_names()

    num_clusters = 10
    km = KMeans(n_clusters=num_clusters, random_state=2)
    km.fit(tfidf_matrix)
    cluster_words_dict = get_cluster_words_dict(reviews, vocab_frame, km, num_clusters, terms)
    cluster_words_dict = manually_define_clusters()
    final_df = clean_df(df, cluster_words_dict, km, users)
    final_df.to_csv(os.path.join('output','data.csv'), index = False)

if __name__ == "__main__":
    main()
