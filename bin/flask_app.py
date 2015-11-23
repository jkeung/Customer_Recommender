#!/usr/bin/env python
import flask
from pymongo import MongoClient

db = MongoClient().yelpdb
collection = db.review_collection
collection2 = db.score_collection

#---------- URLS AND WEB PAGES -------------#

# Initialize the app
app = flask.Flask(__name__, template_folder='../templates', static_folder='../static')

# Homepage
@app.route("/")
def viz_page():
    """
    Homepage: serve our visualization page, awesome.html
    """
    restaurant_lst = []
    cursor = collection2.find()    
    for i in cursor:
        restaurant_lst.append(i)

    return flask.render_template('index.html',
                                title = "Top 10 Places for Pizza in NYC",
                                restaurants = restaurant_lst
                                )

#--------- RUN WEB APP SERVER ------------#

# Start the app server on port 80
# (The default website port)
app.run(host='0.0.0.0', port=8000, debug = True)
