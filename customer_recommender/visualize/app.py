import flask

#---------- URLS AND WEB PAGES -------------#

# Initialize the app
app = flask.Flask(__name__, template_folder='templates', static_folder='static')

# Homepage
@app.route("/")
def viz_page():
    """
    Homepage: serve our visualization page, awesome.html
    """

    return flask.render_template('index.html')
                                
#--------- RUN WEB APP SERVER ------------#

# Start the app server on port 80
# (The default website port)
app.run(host='0.0.0.0', port=5000)