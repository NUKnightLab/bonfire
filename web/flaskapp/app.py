#!/usr/bin/env python
import os
import sys
from flask import Flask, render_template, request, jsonify
from werkzeug.contrib.atom import AtomFeed
from bonfire.db import get_universe_tweets, get_items, search_items, get_recent_top_links
from bonfire.dates import dateify_string, stringify_date, now, apply_offset

app = Flask(__name__)


def clean_params(params):
    # Add tz info so the date parser works (apply the offset later)
    for d in ('start', 'end'):
        if d in params:
            params[d] = params[d][:-4] + '+0000 ' + params[d][-4:]

    # Force the data into a dict with proper types here
    param_map = {
        'term': str,
        'quantity': int,
        'hours': int,
        'start': dateify_string,
        'end': dateify_string,
        'scoring': bool,
        'time_decay': bool
    }
    cleaned_params = {}
    for param, val in params.items():
        if param in param_map:
            val = param_map[param](val)
            cleaned_params[param] = val

    # Keep cleaning the data here
    if 'scoring' in cleaned_params:
        cleaned_params['time_decay'] = cleaned_params.pop('scoring')
    if 'timeOffset' in params:
        offset = int(params.pop('timeOffset'))
        start, end = cleaned_params.get('start'), cleaned_params.get('end')
        cleaned_params['start'] = apply_offset(start, offset)
        cleaned_params['end'] = apply_offset(end, offset)
    return cleaned_params


def respond_json(items):
    response = {
        'status': 'OK',
        'result_count': len(items),
        'items': items
    }
    return jsonify(response)


def respond_html(items, params):
    start, end = None, None
    if 'start' in params:
        start = stringify_date(params['start'])
    else:
        start = stringify_date(now())
    if 'end' in params:
        end = stringify_date(params['end'])
    else:
        end = stringify_date(now())
    kwargs = {
        'universe': universe,
        'links': items,
        'dates': {
            'start': start,
            'end': end
        }
    }
    return render_template('home.html', **kwargs)


def top_links(raw_params):
    params = clean_params(raw_params)
    if 'term' in params:
        args = [params.pop('term')]
        params.pop('hours')
        links = search_items(universe, *args, **params)
    else:
        links = get_items(universe, **params)

    if request.path.endswith('json'):
        return respond_json(links)
    return respond_html(links, params)


@app.route('/get_items.json')
def get_items_json():
    return top_links(request.args)


@app.route('/search_items.json')
def search_items_json():
    return top_links(request.args)


@app.route("/")
def home():
    return day()


@app.route("/fresh/")
def fresh():
    params = dict(request.args.items())
    params['hours'] = 4
    return top_links(params)


@app.route("/day/")
def day():
    params = dict(request.args.items())
    params['hours'] = 24
    return top_links(params)


@app.route("/week/")
def week():
    params = dict(request.args.items())
    params['hours'] = 24 * 7
    params['scoring'] = False
    return top_links(params)


@app.route("/feed/")
def feed():
    feed = AtomFeed('Top links in %s' % universe,
        feed_url=request.url, url=request.url_root)
    links = get_recent_top_links(universe, quantity=20)
    for link in links:
        feed.add(link['title'], unicode(link['description']),
            url=link['url'],
            updated=dateify_string(link['tweet']['created'])
            )
    return feed.get_response()


global universe
if 'BONFIRE_UNIVERSE' in os.environ:
    universe = os.environ.get('BONFIRE_UNIVERSE')

USAGE = """
USAGE:

 $ python app.py <universe>

"""

if __name__ == "__main__":
    try:
        universe = sys.argv[1]
        app.run(debug=True)
    except IndexError:
        print USAGE
