#!/usr/bin/env python3
"""grammalog: a logging.handlers.DatagramHandler collection service

It is quite terrible--blindly unpickling stuff received via untrusted UDP connection...
Future TODO: customize sending end to HMAC the pickle data using a shared secret.
"""
import logging
import pickle
import socket
import struct
import sys
import time

BUF_SIZE = 64*1024

def main(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 1337))
    
    lstderr = logging.StreamHandler()
    lfile = logging.FileHandler("war.log")
    logging.basicConfig(format="%(attacker)s|%(asctime)s|%(message)s",
                        level=logging.INFO,
                        handlers=[lstderr, lfile])
    log = logging.getLogger()
    
    while True:
        payload, (sender, _) = sock.recvfrom(BUF_SIZE)
        attrdict = pickle.loads(payload[4:])    # Skip 4-octect length prefix
        attrdict['attacker'] = sender
        attrdict['created'] = time.time() # Replace time from sender with current time
        record = logging.makeLogRecord(attrdict)
        log.handle(record)

if __name__ == "__main__":
    main(sys.argv[1:])