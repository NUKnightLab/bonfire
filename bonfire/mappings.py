from .dates import ELASTICSEARCH_TIME_FORMAT


RESULTS_CACHE_MAPPING = {
    'properties': {
        'cached_at': {
            'type': 'date',
            'format': ELASTICSEARCH_TIME_FORMAT
        },
        'hours_since': {
            'type': 'integer',
        },
        'results': {
            'properties': {
                '_default_': {
                    'type': 'string',
                    'index': 'no'
                },
                'score': {
                    'type': 'float',
                    'index': 'not_analyzed'
                }
            }
        }
    }
}

CACHED_URL_MAPPING = {
    'properties': {
        'url': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'resolved': {
            'type': 'string',
            'index': 'not_analyzed'
        }
    }
}

TOP_CONTENT_MAPPING = {
    'properties': {
        '_default_': {
            'type': 'string',
            'index': 'no'
        },
        'tweets': {
            'properties': {
                'created': {
                    'type': 'date',
                    'format': ELASTICSEARCH_TIME_FORMAT
                }
            }
        }
    }
}

USER_MAPPING = {
    'properties': {
        'id': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'weight': {
            'type': 'float',
        }
    }
}

CONTENT_MAPPING = {
    'properties': {
        'url': {
            'type': 'string',
            'index': 'not_analyzed'
        }
    }
}

TWEET_MAPPING = {
    'properties': {
        'id': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'content_url': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'created': {
            'type': 'date',
            'format': ELASTICSEARCH_TIME_FORMAT
        },
        'provider': {
            'type': 'string',
            'index': 'not_analyzed'
        }
    }
}

UNPROCESSED_TWEET_MAPPING = {
    'properties': {
        '_default_': {
            'type': 'string',
            'index': 'no'
        },
        'id': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'created_at': {
            'type': 'date',
            'format': ELASTICSEARCH_TIME_FORMAT
        },
    }
}
