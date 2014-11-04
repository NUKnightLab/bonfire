import subprocess
import datetime
from bonfire.db import get_latest_raw_tweet

def main():
        if get_latest_raw_tweet('journotech'):
            pass
            # print 'bonfire collect queue not empty'
        else:
            print '%s restarting bonfire collect' % datetime.datetime.utcnow().isoformat()
            subprocess.call('service bonfire-collect restart', shell=True)


if __name__=='__main__':
    main()
