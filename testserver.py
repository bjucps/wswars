#!/usr/bin/env python3
"""warproxy Test Server

Dummy HTTP/1.0 server (GET verb only) used to test the WarProxy.
"""
import argparse
import http.server
import logging
import os
import socketserver
import threading
import time

class TestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    
    def do_GET(self):
        if self.server.hung:
            # Wait forever...
            while True:
                time.sleep(60)
        
        # "Special" behaviors to test proxy edge cases/scoring
        if self.path == "/fail/hang":
            # Silently stop responding to future requests
            self.server.hung = True
        elif self.path == "/fail/boom":
            # Terminate server with extreme prejudice!!!
            os._exit(42)
        
        # Normal request behavior (look for file)
        path = self.path[1:] if self.path[0] == '/' else self.path
        full_path = os.path.join(self.server._doc_root, path)
        real_path = os.path.realpath(full_path)
        if not real_path.startswith(self.server._doc_root):
            logging.warning("Requested file '{0}' NOT inside doc-root ('{1}')".format(real_path, self.server._doc_root))
            self.send_response(403, "Forbidden")
            self.end_headers()
            return
        
        try:
            with open(real_path, "rb") as fd:
                contents = fd.read()
        except FileNotFoundError:
            self.send_response(404, "Not Found")
            self.end_headers()
        except Exception:
            self.send_response(500, "Server Error")
            self.end_headers()
        else:
            # Send vanilla 200 response
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(contents)
    
    def handle_one_request(self):
        try:
            super().handle_one_request()
        finally:
            self.server.worker_done()
    
    def log_message(self, fmt, *args):
        logging.info(fmt%args)

class TestServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, doc_root, max_workers):
        super().__init__(server_address, RequestHandlerClass)
        self._doc_root = os.path.realpath(doc_root)
        self._max_workers = max_workers
        self._worker_count = 0
        self._worker_lock = threading.Lock()
        
        # Special behavior flag
        self.hung = False
    
    def worker_done(self):
        with self._worker_lock:
            self._worker_count -= 1
            logging.info("Worker finished; down to {0} workers...".format(self._worker_count))
    
    def verify_request(self, request, client_address):
        with self._worker_lock:
            if self._worker_count >= self._max_workers:
                logging.warning("Request from {0} would exceed worker limit of {1}; dropping...".format(client_address, self._max_workers))
                return False
            else:
                self._worker_count += 1
                logging.info("New request (from {0}); {1} workers active...".format(client_address, self._worker_count))
                return True

def main():
    logging.basicConfig(level=logging.INFO)
    
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("-p", "--port", type=int, default=5000, help="TCP port on which to listen.")
    ap.add_argument("-h", "--host", default="localhost", help="Hostname/IPv4 address on which to listen.")
    ap.add_argument("-w", "--workers", type=int, default=10, help="Max number of simulataneous requests.")
    ap.add_argument("-r", "--root", default=".", help="Document root folder.")
    args = ap.parse_args()
    print(args)
    
    TestServer((args.host, args.port), TestHandler, args.root, args.workers).serve_forever()

if __name__ == "__main__":
    main()

