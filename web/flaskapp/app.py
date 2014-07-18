import sys
from flask import Flask, render_template, request
from bonfire.db import get_universe_tweets, get_popular_content, search_content

app = Flask(__name__)


@app.route("/")
def home():
    since_map = {
        'superfresh': 1,
        'fresh': 4,
        'day': 24,
        'week': 24 * 7
    }
    # Default to showing the last day
    since = since_map[request.args.get('since', 'day')]

    if request.args.get('tweetsearch'):
        content = search_content(request.args.get('tweetsearch'), size=20)
    else:
        content = get_popular_content(universe, since=since, size=20)
    tweets = get_universe_tweets(universe, request.args.get('tweetsearch'), since=since, size=20)

    return render_template('home.html',
        universe = universe,
        tweets   = tweets,
        content  = content
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
