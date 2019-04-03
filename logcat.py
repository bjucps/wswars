#!/usr/bin/python3

import sys
import re
import time

users = {}
with open('/home/cps320/wswars/users.txt') as f:
    for line in f:
        [username, ipaddr] = line.strip().split(' ')
        users[ipaddr] = username

def tail(theFile):
    #theFile.seek(0,2)   # Go to the end of the file
    while True:
        line = theFile.readline()
        if not line:
            print('.', end='')
            sys.stdout.flush()
            time.sleep(2)    # Sleep briefly for 10sec
            continue
        print('\r', end='')
        yield line

lastsrc, lastdest, lastresult = '', '', ''
for line in tail(open(sys.argv[1])):
    #print(line)
    [destip, datestr, _, _, msg] = line.split('|')
    if destip in users:
        destip = users[destip]
    #print(msg)
    match = re.search('Attack from ([^ ]+)', msg)
    if match:
        
        srcip = match.group(1)
        if srcip in users:
            srcip = users[srcip]
        if 'KILL' in msg:
            result = 'KILL'
        elif 'HUNG' in msg:
            result = 'HUNG SERVER'        
        else:
            continue
        
        if srcip != lastsrc or destip != lastdest or lastresult != result:
            print('{} {} attacked by {} resulted in {}'.format(datestr, destip, srcip, result))
        lastsrc, lastdest, lastresult = srcip, destip, result


