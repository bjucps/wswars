#!/usr/bin/env python3
"""warproxy Test Client

Simple HTTP client for "attacking" the test server via the WarProxy.
"""
import cmd
import http.client
import logging
import socket
import threading
import time

class MyConn(http.client.HTTPConnection):
    _http_vsn = 10
    _http_vsn_str = 'HTTP/1.0'
    auto_open = 0

class Attacker(cmd.Cmd):
    intro = ""
    prompt = ""
    
    def __init__(self, name="attacker", stdin=None):
        super().__init__(stdin=stdin)
        if stdin:
            self.use_rawinput = False
        
        self._log = logging.getLogger(name)
        
        self._timeout = None
        self._src = None
        self._dst = None
        self._conns = {}
    
    def emptyline(self):
        pass
    
    def do_timeout(self, argline):
        '''Set timeout for future HTTP connections in seconds.
        
        Syntax: timeout SECONDS
        
        Example: timeout 5.0
        '''
        if not argline.strip():
            self._log.info("Current timeout: {0}".format(self._timeout))
            return
        
        try:
            self._timeout = float(argline)
        except:
            self._log.exception("Unable to parse timeout:")
    
    def do_source(self, argline):
        '''Bind to a particular socket name as the source of future connections.
        
        Syntax: source HOSTNAME [PORTNAME="0"]
        
        Example: source 127.0.1.1 2222
        
        Note that if you intend to create multiple connections, you should
        leave PORTNAME to its default value of "0" (auto-select at connect time),
        since you cannot, of course, have more than one connection with the same
        source (host:port) address...
        '''
        if not argline.strip():
            self._log.info("Current source: {0}".format(self._src))
            return
        
        try:
            hostname, portname = argline.split()
        except ValueError:
            hostname, portname = argline, "0"
        
        try:
            info = socket.getaddrinfo(hostname, portname, family=socket.AF_INET, type=socket.SOCK_STREAM)[0]
        except:
            self._log.exception("Error parsing bind parameters:")
        else:
            self._src = info[-1]
            self._log.info("Binding to ({0}, {1}) for future connections".format(self._src[0], self._src[1]))
    
    def do_target(self, argline):
        '''Set target address for future connections.
        
        Syntax: target HOSTNAME [PORTNAME="80"]
        
        Example: target localhost 5000
        '''
        if not argline.strip():
            self._log.info("Current target: {0}".format(self._dst))
            return
            
        try:
            hostname, portname = argline.split()
        except ValueError:
            hostname, portname = argline, "80"
        
        try:
            info = socket.getaddrinfo(hostname, portname, family=socket.AF_INET, type=socket.SOCK_STREAM)[0]
        except:
            self._log.exception("Error parsing target parameters:")
        else:
            self._dst = info[-1]
            self._log.info("Connecting to ({0}, {1}) for future connections".format(self._dst[0], self._dst[1]))
    
    def do_list(self, argline):
        '''List current connections.
        '''
        for name in sorted(self._conns):
            try:
                sock = self._conns[name].sock
                self._log.info("{0}: {1} -> {2}".format(name, sock.getsockname(), sock.getpeername()))
            except:
                self._log.exception("Error printing connection '{0}'".format(name))
    
    def do_connect(self, argline):
        '''Open a [named] connection from source to target.

        Syntax: connect [NAME="default"]
        
        Example: connect c1
        '''
        name = argline.strip()
        if not name:
            name = "default"
        
        if name in self._conns:
            self._log.error("Connection named '{0}' already exists!".format(name))
        else:
            try:
                self._conns[name] = MyConn(self._dst[0], self._dst[1], self._timeout, source_address=self._src)
                self._conns[name].connect()
            except:
                self._log.exception("Unable to establish connection:")
    
    def do_close(self, argline):
        '''Close a previously opened connection.
        
        Syntax: close [NAME="default"]
        
        Example: close c1
        '''
        name = argline.strip()
        if not name:
            name = "default"
        
        try:
            self._log.info("Closing/deleting connection '{0}'".format(name))
            self._conns[name].close()
            del self._conns[name]
        except KeyError:
            self._log.error("No such connection '{0}'".format(name))
        except:
            self._log.exception("Error closing connection:")
    
    def do_get(self, argline):
        '''Request an HTTP resource via an opened connection.
        
        Syntax: get [NAME="default"] PATH
        '''
        try:
            name, path = argline.split()
        except ValueError:
            name, path = "default", argline.strip()
        
        try:
            conn = self._conns[name]
        except KeyError:
            self._log.error("No such connection '{0}'".format(name))
        else:
            try:
                self._log.info("Requesting '{0}' with GET on '{1}'".format(path, name))
                conn.request("GET", path)
                
                response = conn.getresponse()
                self._log.info("Response: {0} '{1}'".format(response.status, response.reason))
                self._log.debug("Response Body:\n\t" + b'\t'.join(response.read().split(b'\n')).decode('utf-8'))
                
                self._log.info("Closing/deleting connection '{0}'".format(name))
                conn.close()
                del self._conns[name]
            except:
                self._log.exception("Error sending request/getting response:")
    
    def do_pause(self, argline):
        '''Pause for SECONDS seconds: pause 0.5'''
        try:
            delay = float(argline)
        except:
            self._log.exception("Unable to parse pause arguments:")
        else:
            time.sleep(delay)
    
    def do_bye(self, argline):
        '''Quit.'''
        return True
    do_EOF = do_bye

def script_runner(stdin_filename):
    with open(stdin_filename, "rt", encoding="ascii") as stdin:
        Attacker(name=stdin_filename, stdin=stdin).cmdloop()

def main(args):
    if not args:
        Attacker().cmdloop()    # Interactive mode, from STDIN
    else:
        threads = [threading.Thread(target=script_runner, args=(filename,)) for filename in args]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
