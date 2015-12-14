#!/bin/bash

python -m customer_recommender.ingest.yelp
python -m customer_recommender.wrangle.cluster_data
