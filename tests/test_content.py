import sys
import csv
from bonfire import content

def urls_to_csv(infile='infile.txt', outfile='outfile.csv'):
    with open(infile, 'r') as f:
        urls = f.read().split('\n')

    utfize = lambda d: dict([(k, v.encode('utf-8') \
             if hasattr(v, 'encode') and isinstance(v, unicode) else v) \
             for k,v in d.items()])

    results = []
    for index, url in enumerate(urls):
        print 'Now on url %d (%s)' % (index, url)
        try:
            result = content.extract(url)
        except Exception as e:
            '\t%s FAILED %s, %s' % (url, e, e.message)
            continue
        result.pop('raw_html')
        results.append(utfize(result))
    
    with open(outfile, 'w+') as f:
        writer = csv.DictWriter(f, results[0].keys())
        writer.writeheader()
        writer.writerows(results)

if __name__ == '__main__':
    """Takes a list of URLs in a txt file, runs through extractor, and spits out csv."""
    if len(sys.argv) == 3:
        run(infile=sys.argv[1], outfile=sys.argv[2])
    elif len(sys.argv) == 2:
        run(infile=sys.argv[1])
    else:
        run()