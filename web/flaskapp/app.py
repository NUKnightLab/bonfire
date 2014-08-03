#!/usr/bin/env python
import sys
import datetime
from flask import Flask, render_template, request, jsonify
from werkzeug.contrib.atom import AtomFeed
from bonfire.db import get_universe_tweets, get_items, search_items, get_recent_top_links

app = Flask(__name__)

TIME_FORMAT = '%Y/%m/%d %H:%M'


def convert_time(datestr, time_format=TIME_FORMAT):
    return datetime.datetime.strptime(datestr, time_format) if datestr else None


def time_to_string(dt, time_format=TIME_FORMAT):
    return dt.strftime(time_format) if dt else ''


def clean_params(params):
    param_map = {
        'term': str,
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
def get_items_json():
    params = clean_params(request.args)
    links = get_items(universe, **params)
    response = create_response(links)
    return jsonify(response)


@app.route('/search_items.json')
def search_items_json():
    params = clean_params(request.args)
    args = [params.pop('term')]
    links = search_items(universe, *args, **params)
    response = create_response(links)
    return jsonify(response)


def top_links(since=None, quantity=20):
    if since is None:
        start = convert_time(request.args.get('startdate'))
        end = convert_time(request.args.get('enddate'))
    else:
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(hours=since)

    if request.args.get('search'):
        links = search_items(universe, request.args.get('search'), quantity=quantity)
    else:
        links = get_items(universe, quantity=quantity)
    tweets = get_universe_tweets(universe, request.args.get('search'), start=start, end=end, size=quantity)
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


@app.route("/feed/")
def feed():
    feed = AtomFeed('Top links in %s' % universe,
        feed_url=request.url, url=request.url_root)
    links = get_recent_top_links(universe, quantity=20)
    for link in links:
        author = link['authors']
        if not author:
            author = link['twitter_creator'] or link['tweet']['user_screen_name']
            if not author.startswith('@'):
                author = '@' + author
        updated = convert_time(link['tweet']['created'].replace('+0000 ', ''), '%a %b %d %H:%M:%S %Y')
        feed.add(link['title'], unicode(link['description']),
            url=link['url'],
            updated=updated
            )
    return feed.get_response()


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
