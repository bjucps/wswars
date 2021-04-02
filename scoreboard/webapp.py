#!/usr/bin/python3

# Test Usage: ./webapp.py -r ../users.txt.sample  -p 8000

import bottle
from  threading import Thread
import requests
import time
import subprocess

REGISTER_FILENAME = '/home/cps250/wswars/users.txt'
RESPONSE_TEXT = 'Hello, world!'
LOGFILE = '../war.log'

warriorStats = {} # see makeStats for format of entries
ipToUsername = {}
killLog = []

def makeStats(ip):
    return {'ip': ip, 'status': 'Offline', 'attacks': 0, 'kills': [], 'survives': 0, 'killedby': []}

class ProbeThread(Thread):
    def __init__(self, register_file, warlog):
        super().__init__()
        self.f = subprocess.Popen(['tail','-F','-n', '+1',warlog], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.register_file = register_file

    def readRegisteredUsers(self):
        global ipToUsername, usernameToIp
        ipToUsernameLocal = {}
        try:
            with open(self.register_file) as f:
                for line in f:
                    [username, ip, handle] = line.strip().split(' ')
                    ipToUsernameLocal[ip] = handle
                    if handle in warriorStats:
                        warriorStats[handle]['ip'] = ip

        except Exception as e:
            print(e)

        ipToUsername = ipToUsernameLocal

    def processRecord(self, sourceIp, timeStamp, msgType, msgInfo):
        if sourceIp not in ipToUsername:
            return

        sourceUser = ipToUsername[sourceIp]
        if sourceUser not in warriorStats:
            warriorStats[sourceUser] = makeStats(sourceIp)

        stats = warriorStats[sourceUser]
        if msgType == 'STATUS':
            stats['status'] = msgInfo
        elif msgType == 'ATTACK':
            [attackerIp, result] = msgInfo.split(':')
            if result == 'OK':
                stats['survives'] += 1

            if attackerIp in ipToUsername:                
                attacker = ipToUsername[attackerIp]
                if attacker not in warriorStats:
                    warriorStats[attacker] = makeStats(attackerIp)
                if warriorStats[attacker]['status'] != 'Online':
                    return
                warriorStats[attacker]['attacks'] += 1
                if result != 'OK' and attacker not in stats['killedby']:                    
                    stats['killedby'].append(attacker)
                    warriorStats[attacker]['kills'].append(sourceUser)
                    killLog.append((attacker, sourceUser, timeStamp))


    def run(self):
        lastCheck = 0
        startTime = time.time()
        while True:
            now = time.time()
            line = self.f.stdout.readline().decode('utf-8').strip()
            print("Got: " + line)
            if lastCheck + 5 < now:
                self.readRegisteredUsers()
                lastCheck = now
            [sourceIp, timeStamp, msgType, msgInfo] = line.split('|')
            self.processRecord(sourceIp, timeStamp, msgType, msgInfo)
            if now - startTime > 5:
                # Don't lines loaded during startup
                print(line)


    # # Not used
    # def pingParticipants(self):
    #     while True:
    #         for i in range(len(users)):
    #             [username, ip] = users[i]
    #             URL = 'http://{}:8080/test.txt'.format(ip)
    #             success = 0
    #             try:
    #                 response = requests.get(URL, timeout=.5)
    #                 success = 1
    #                 txt = response.text.strip()
    #                 if txt == RESPONSE_TEXT:
    #                     success = 2
    #                 else:
    #                     print(username, "returned", txt)
    #             except Exception as e:
    #                 print(username, ':', e)
    #             users[i] = [username, success]
    #         self.result = users
    #         time.sleep(5)

# CODES = ['Connect failed', 'Incorrect response', 'OK']

@bottle.route('/')
def home():
    hlist = ''
    localStats = warriorStats
    sortlist = []
    for warrior in localStats.keys():
        stats = localStats[warrior]
        sortlist.append((1000 - len(stats['kills']), 10000000 - stats['survives'], warrior))
    for (_,_,warrior) in sorted(sortlist):
        stats = localStats[warrior]
        ip = stats['ip']
        status = stats['status']
        status = f'<span class="{status}">{status}</span>'
        attacks = stats['attacks']
        kills = len(stats['kills'])
        survives = stats['survives']
        killedBy = ','.join(stats['killedby'])
        hlist += f"""<tr><td>{warrior}
        <td><a href="http://{ip}:8080/" target="_blank">{ip}</a>
        <td>{status}
        <td>{attacks}
        <td>{kills}
        <td>{survives}
        <td>{killedBy}
        """
    LAST_KILL_COUNT = 15
    if len(killLog) < LAST_KILL_COUNT:
        killLogLast = killLog
    else:
        killLogLast = killLog[-LAST_KILL_COUNT:]
    killLogLast.reverse()

    killStr = ""
    for (attacker, victim, timestamp) in killLogLast:
        killStr += f"{timestamp} - {attacker} killed {victim}<br>"
    return HTML.format(hlist, killStr)

@bottle.route('/resources/<filename:path>')
def send_static(filename):
    """Helper handler to serve up static game assets.
    
    (Borrowed from BottlePy documentation examples.)"""
    return bottle.static_file(filename, root='./resources')


HTML = """
<html>
<head>
<meta http-equiv="refresh" content="5">
<style>
body {{ background-color: black; color: white; margin: 50px; font-size: 14pt }}
table {{
    border-collapse: collapse;
    float: left;
    margin-right: 50px;
    width: 1000;
}}

td, th {{
    border: 1px solid white;
    padding: 3px;
    font-size: 14pt;
    text-align: center;
}}
a {{ color: white }}
.Offline {{ color: red }}
.Online {{ color: green }}
</style>
</head>
<body>
<img src='/resources/webserverwars.png'>
<table>
<tr>
    <th>Warrior</th>
    <th>IP</th>
    <th>Status</th>
    <th>Attacks</th>
    <th>Kills</th>
    <th>Survives</th>
    <th style='width: 40%'>Killed by</th>
</tr>
{}
</table>
<div>
{}
</div>
</body>
</html>
"""

if __name__ == '__main__':
    import argparse
    from sys import argv
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--register-file", default=REGISTER_FILENAME, help="Register filename")
    ap.add_argument("-l", "--warlog", default=LOGFILE, help="War log filename")
    ap.add_argument("-p", "--port", default=8000, help="Scoreboard port number")
    args = ap.parse_args(argv[1:])
    
    pt = ProbeThread(args.register_file, args.warlog)
    pt.start()
    bottle.run(host='', port=int(args.port))

