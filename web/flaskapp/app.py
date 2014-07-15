import sys
from flask import Flask, render_template, request
from bonfire.db import get_universe_tweets, search_universe_tweets

app = Flask(__name__)


@app.route("/")
def home():
    if 'tweetsearch' in request.args:
        tweets = search_universe_tweets(universe, request.args.get('tweetsearch'), size=20)
    else:
        tweets = get_universe_tweets(universe, size=20)
    return render_template('home.html',
        universe=universe,
        tweets = tweets,
    )


USAGE = """
USAGE:

 $ python app.py <universe>

"""

if __name__ == "__main__":
    global universe
    try:
        universe = sys.argv[1]
        app.run(debug=True)
    except IndexError:
        print USAGE
