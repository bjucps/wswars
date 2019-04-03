#!/usr/bin/env python3
import http.client
import logging
import socket
import subprocess
import sys

class Warden:
    '''Launches and stands watch over a webserver process.
    
    Assumes a compliant CpS 320 webserver that accepts the following options:
    
        ./executable_name [OTHER OPTIONS] -h HOSTNAME -p PORT
    '''
    
    log = logging.getLogger("warden")
    
    # How long to wait for a local server response
    TIMEOUT = 0.1   # Seconds
    
    def __init__(self, exec_args, logfile_name="webserver.log", listen_host="localhost", listen_port=5000):
        '''Spawn the process so it can be monitored.
        
        execargs: a list of strings suitable for use with subprocess.Popen
                    (will have ['-h', <listen_host>, '-p', <listen_port>] appended to it)
        '''
        self._listen_host = listen_host
        self._listen_port = int(listen_port)    # Make sure we can increment this to avoid "address in use" errors on respawn
        self._logfile_name = logfile_name
        self._exec_args = exec_args
        
        self._proc = None
        self._respawn()
    
    def __del__(self):
        if self._proc:
            self._proc.kill()
    
    @property
    def address(self):
        '''What (host, port) to forward connections to.'''
        return (self._listen_host, self._listen_port)
    
    def _respawn(self):
        ''' Internal helper to actually [re-]launch the webserver.'''
        args = self._exec_args + ['-h', self._listen_host, '-p', str(self._listen_port)]
        try:
            self.log.info("Spawning webserver (logging to {0})".format(self._logfile_name))
            with open(self._logfile_name, "ab") as logfile:
                self._proc = subprocess.Popen(args,
                                stdin=subprocess.DEVNULL,
                                stdout=logfile,
                                stderr=subprocess.STDOUT)
        except:
            self.log.exception("Error spawning webserver process:")
            self._proc = None
            raise   # Don't try to contain it, just log it on the way out
    
    def _request(self, path, timeout):
        '''Internal helper to request a resource from the server.
        
        Used to qualify contestants and to ping the server for responsiveness.
        Returns response object on success, None on failure (logs all details).
        '''
        try:
            self.log.debug("Hitting ({0}:{1}) with a 'GET {2}' request...".format(self._listen_host, self._listen_port, path))
            conn = http.client.HTTPConnection(self._listen_host, self._listen_port, timeout)
            conn.request("GET", path)
            resp = conn.getresponse()
            self.log.debug("...got {0} ({1}) response!".format(resp.status, resp.reason))
            return resp
        except socket.timeout:
            # So it's not responding...
            self.log.debug("Server did not respond (request timeout)!")
            return None
        except:
            # This is interesting...
            self.log.exception("Error requesting resource:")
            return None
    
    def check(self, get_path="/test.txt", timeout=TIMEOUT) -> tuple:
        '''Check the processes for both liveness and responsiveness.
        
        If the process is dead: respawn, and return (True, dead_status_code).
        If the process is hung (timeout on test request): kill it, respawn it, and return (True, None).
        Otherwise, return (False, None).
        '''
        # Check for hung server
        resp = self._request(get_path, timeout)
        if (not resp) or (resp.status != 200):
            # Whatever happened, we're going to respawn--so bump our local-listen port
            # to avoid stupid "address in use" errors on server startup
            self._listen_port += 1
            
            # Check for process death...
            exit_status = self._proc.poll()
            if exit_status is not None:
                self.log.info("webserver DIED (status={0}); respawning...".format(exit_status))
                self._respawn()
                return (True, exit_status)
            else:
                self.log.info("webserver not responding [properly] (status={0}); bouncing...".format(getattr(resp, "status", None)))
                try:
                    self._proc.kill()
                except:
                    self.log.exception("Error killing webserver process:")
                self._respawn()
                return (True, None)
        
        # All checks passed!
        return (False, None)

INSTRUCTIONS = """\
Instructions:

    Copy your webserver executable (e.g., "webserver") into this folder
    (i.e., the folder containing qualify.py and test.txt).

    Make sure qualify.py is executable (e.g., chmod +x qualify.py).
    
    Then use this program to launch your webserver, like this:
    
    ./qualify.py ./webserver
    
    The program will tell you whether or not your server "qualifies."
"""
        
def main(argv):
    if len(argv) == 1:
        print(INSTRUCTIONS)
        return
    
    warden = Warden(argv[1:], listen_host="localhost", listen_port=5005)
    down, status = warden.check(timeout=10.0)    # Give the server process longer to spin up before the first ping
    if down:
        print("\n*** ERROR: the webserver was not successfully launched (or isn't properly configured to serve up /test.txt)", file=sys.stderr)
        sys.exit(1)
    
    print("\n*** OK! Your webserver should qualify for the Wars...")

if __name__ == "__main__":
    main(sys.argv)
