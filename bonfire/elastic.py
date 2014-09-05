"""
An attempt to make the Elasticsearch client a bit more usable. Currently
implements `search`, `get`, and `mget`. `get_source` maps to `get` because there
really should not be a need for both if the API is done correctly. For the time
being, other client methods will behave just as they do for the client provided
by Elasticsearch.

The implemented methods return ESDocument or ESCollection objects. ESDocument is
dot-addressable and dict-like. It's keys are your document keys. Meta-data is
attached to this document with underscored properties: _index, _type, _id, and
when applicable: _score, _version, _found. I realize that `_` has the general
connotation of "privacy" in Python, but this seems to me to be the safest way to
have special keys and keep the API fairly usable.

ESCollection is an iterable of those documents and has the special properties:
took, timed_out, total_shards, successful_shards, failed_shards. No need for
['hits']['hits'] deferencing -- just iterate the collection. Same for ['docs']
on an mget operation.
"""
from elasticsearch import Elasticsearch


class ESCollection(object):

    def __init__(self, resultset):
        """Construct an Elasticsearch Collection on a result set from the
        Elasticsearch Python client.

        Collection is iterable of Elasticsearch documents. Abstracts the
        concepts of hits (for searches) and docs (for mget) into the singular
        concept of an iterable collection.

        Collection also has the following parameters which are set as
        appropriate (i.e. when provided by Elasticsearch):

        took
        timed_out
        total_shards
        successful_shards
        failed_shards
        total_hits
        max_score
        """
        self.aggregations = ESAggregation(resultset.get('aggregations', {}))
        self.took = resultset.get('took')
        self.timed_out = resultset.get('timed_out')
        _shards = resultset.get('_shards')
        if _shards is not None:
            self.total_shards = _shards['total']
            self.successful_shards = _shards['successful']
            self.failed_shards = _shards['failed']
        else:
            self.total_shards = self.successful_shards = self.failed_shards = \
                None
        _hits = resultset.get('hits')
        if _hits is not None:
            self.total_hits = _hits['total']
            self.max_score = _hits['max_score']
            self._hits = (hit for hit in _hits['hits'])
        else:
            self._hits = (doc for doc in resultset.get('docs'))

    def __iter__(self):
        return self

    def next(self):
        return ESDocument(self._hits.next())


class ESAggregation(dict):

    def __getattr__(self, name):
        if name in self.iterkeys():
            r = self[name]
            if isinstance(r, dict):
                if r.keys() == [u'buckets']:
                    return ESAggregation({
                        bucket['key']: ESAggregation(bucket) for bucket in
                            r['buckets'] })
                else: 
                    return ESAggregation(r)
            elif isinstance(r, list):
                return [ ESAggregation(i) for i in r ]
            else:
                return r

        raise AttributeError('%s has no property named %s.' % (
            self.__class__.__name__, name))


class ESDocument(dict):

    def __init__(self, doc):
        """Construct a dict-like dot-addressable document object from an
        Elasticsearch hit or doc result.

        Contains the following 'meta' properties:
        _index
        _type
        _id
     
        And optional meta-properties (Set to None if not applicable):
        _score
        _version
        _found

        Important Note: This means you should not name properties on your
        documents with the above property names!
        """
        self._index = doc['_index']
        self._type = doc['_type']
        self._id = doc['_id']

        self._score = doc.get('_score') # only applicable for searches
        self._version = doc.get('_version') # don't get this in searches
        self._found = doc.get('found') # comes with `get` operation - but not
                                       # sure why since get throws NotFoundError
        # Empty _source supported for _source=False client requests
        super(ESDocument, self).__init__(doc.get('_source', {}))

    def __getattr__(self, name):
        if name in self.iterkeys():
            return self[name]
        raise AttributeError('%s has no property named %s.' % (
            self.__class__.__name__, name))



class ESClient(Elasticsearch):

    def search(self, *args, **kwargs):
        res = super(ESClient, self).search(*args, **kwargs)
        return ESCollection(res)

    def get(self, *args, **kwargs):
        return ESDocument(super(ESClient, self).get(*args, **kwargs))

    def get_source(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def mget(self, *args, **kwargs):
        return ESCollection(super(ESClient, self).mget(*args, **kwargs))


if __name__=='__main__':

    client = ESClient()

    ## Some examples

    # print all content ids and urls
    res = client.search(index='bonfire', doc_type='content', body={})
    for r in res:
        print r._id
        print r.url

    # get a specific content document
    r = client.get(index='bonfire', id='http://www.scientificamerican.com/article/rats-experience-feelings-of-regret', doc_type='content')
    print r._id
    print r.url
    print r._version
    print r._found

    # get several content documents by id
    ids = [
        'http://www.scientificamerican.com/article/rats-experience-feelings-of-regret',
        'http://www.wcvb.com/money/massachusetts-hottest-real-estate-towns/27182216',
        'http://digitalhumanitiesnow.org/2014/07/job-paul-mellon-centre-vacancies',
        'http://nytimesmarketing.com/op-doc-submit' ]
    res = client.mget(index='bonfire', body={ 'ids': ids }, doc_type='content')
    for r in res:
        print r.url
