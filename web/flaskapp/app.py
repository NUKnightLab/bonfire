import sys
from flask import Flask, render_template, request, jsonify
from bonfire.db import get_universe_tweets, get_popular_content, search_universe_content

app = Flask(__name__)


def top_links(since=24, size=20):
    if request.args.get('search'):
        links = search_universe_content(universe, request.args.get('search'), since=since, size=size)
    else:
        links = get_popular_content(universe, since=since, size=size)
    tweets = get_universe_tweets(universe, request.args.get('search'), since=since, size=size)
    kwargs = {
        'universe': universe,
        'tweets': tweets,
        'links': links
    }
    
    mimetype = 'json' if request.path.endswith('json') else 'html'
    if mimetype == 'html':
        return render_template('home.html', **kwargs)
    elif mimetype == 'json':
        return jsonify(kwargs)

@app.route("/")
@app.route("/day/")
@app.route("/day.json")
def day():
    return top_links(since=24)

@app.route("/fresh/")
@app.route("/fresh.json")
def fresh():
    return top_links(since=4)

@app.route("/week/")
@app.route("/week.json")
def week():
    return top_links(since=24 * 7)


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
