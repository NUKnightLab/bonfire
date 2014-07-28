import sys
import datetime
from flask import Flask, render_template, request, jsonify
from bonfire.db import get_universe_tweets, get_links, search_universe_content

app = Flask(__name__)

TIME_FORMAT = '%Y/%m/%d %H:%M'


def convert_time(datestr):
    return datetime.datetime.strptime(datestr, TIME_FORMAT) if datestr else None


def time_to_string(dt):
    return dt.strftime(TIME_FORMAT) if dt else ''


def clean_params(params):
    param_map = {
        'quantity': int,
        'hours': int,
        'daterange': tuple,
        'scoring': bool
    }
    cleaned_params = {}
    for param, val in params.items():
        if param in param_map:
            val = param_map[param](val)
        cleaned_params[param] = val
    if 'daterange' in cleaned_params:
        for index, item in cleaned_params['daterange']:
            cleaned_params['daterange'][index] = convert_time(item)
    return cleaned_params


def create_response(items):
    response = {
        'status': 'OK',
        'result_count': len(items),
        'items': items
    }
    return response


@app.route('/get_items.json')
def get_items():
    params = clean_params(request.args)
    links = get_links(universe, **params)
    response = create_response(links)
    return jsonify(response)


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
        links = get_links(universe)
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
