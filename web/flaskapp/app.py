import sys
import datetime
from flask import Flask, render_template, request, jsonify
from bonfire.db import get_universe_tweets, get_popular_content, search_universe_content

app = Flask(__name__)

def convert_time(datestr):
    return datetime.datetime.strptime(datestr, '%Y/%m/%d %H:%M') if datestr else None
def time_to_string(dt):
    return dt.strftime('%Y/%m/%d %H:%M') if dt else ''

def top_links(since=None, size=20):
    if since is None:
        start = convert_time(request.args.get('startdate'))
        end = convert_time(request.args.get('enddate'))
    else:
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(hours=since)

    if request.args.get('search'):
        links = search_universe_content(universe, request.args.get('search'), start=start, end=end, size=size)
    else:
        links = get_popular_content(universe, start=start, end=end, size=size)
    tweets = get_universe_tweets(universe, request.args.get('search'), start=start, end=end, size=size)
    kwargs = {
        'universe': universe,
        'tweets': tweets,
        'links': links,
        'dates': {
            'start': time_to_string(start),
            'end': time_to_string(end)
        }
    }
    
    mimetype = 'json' if request.path.endswith('json') else 'html'
    if mimetype == 'html':
        return render_template('home.html', **kwargs)
    elif mimetype == 'json':
        return jsonify(kwargs)

@app.route("/")
def home():
    if not request.args.get('startdate'):
        since = 24
    else:
        since = None
    return top_links(since=since)

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
