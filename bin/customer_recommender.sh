#!/bin/bash

# get data and store in database
python -m customer_recommender.ingest.yelp

# creates clusters
python -m customer_recommender.wrangle.cluster_data

# launches Flask app
python customer_recommender/visualize/app.py 

