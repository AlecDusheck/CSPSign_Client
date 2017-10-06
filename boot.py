import urllib3
import requests
import subprocess
import time
import sched
import os
import shutil

# CONFIG

childProc = None
versionPath = 'ver.conf'
apiKeyPath = 'apiKey.conf'

updateInterval = 3600


# END CONFIG

# check current version from server ====
def getCurrentVersion():
    str = open(versionPath, 'r').read()
    json_data = requests.get('https://apcspsign.azurewebsites.net/api/currentVersion').json()
    formatted_ver = json_data['currentVersion']
    return formatted_ver
    # check current version from server ====


# check in ====
def checkIn():
    str = open(versionPath, 'r').read()

    apiKey = open(apiKeyPath, 'r').read()
    apiKey = ''.join(apiKey.split())
    apiKey = apiKey.replace(" ", "")

    json_data = requests.get('https://apcspsign.azurewebsites.net/api/private/checkIn?key=' + apiKey).json()
    formatted_ver = json_data['status']
    if (formatted_ver == 'OK'):
        print('Checking in with server.. OK')
    else:
        print('Checking in with server.. FAILED, Bad api key?')
        # check in ====


# check update ====
def checkUpdate():
    print('Contacting server for update..')
    currentVersion = getCurrentVersion()

    # compare the most recent file to the current one
    if (open(versionPath, 'r').read() != currentVersion):
        print(' Found a update. Auto-installing update. ')
        global childProc
        childProc.terminate()
        http = urllib3.PoolManager()
        with http.request('GET', "http://apcspsign.azurewebsites.net/api/download", preload_content=False) as r, open(
                "load.py", 'wb') as out_file:
            shutil.copyfileobj(r, out_file)

        print(' Got update. Starting child process.. ')
        argument = '...'
        proc = subprocess.Popen(['python', 'load.py', argument], shell=True)
        time.sleep(3)
        pid = proc.pid
        childProc = proc
        # overwrite old ver file
        wr = open(versionPath, 'w')
        wr.write(currentVersion)

        print(' Restarted child process.. ')
    else:
        print(
            ' We are already using the latest version (REL-prod-' + currentVersion + '). ')
        # check update ====


# BOOT ====

print(' AP CSP SIGN Loading.. ')
checkIn()
checkUpdate()
print('Getting the time..')
json_data = requests.get('https://apcspsign.azurewebsites.net/api/time').json()
os.system("w timedatectl set-ntp 0")
os.system("w date --set \"" + json_data['currentTime'] + "\"")
print("Updated local clock with command: date --set \"" + json_data['currentTime'] + "\"")

argument = '...'
proc = subprocess.Popen(['python3', 'load.py', argument], shell=True)
print('Loaded child process..')
print('Update interval set to ' + str(updateInterval))
time.sleep(3)
pid = proc.pid
childProc = proc

# BOOT ====

# update check routine ====
s = sched.scheduler(time.time, time.sleep)


def checkUpdateSh(sc):
    checkUpdate()
    s.enter(updateInterval, 1, checkUpdateSh, (sc,))


s.enter(updateInterval, 1, checkUpdateSh, (s,))
s.run()
# update check routine ====
# checkin routine ====
s = sched.scheduler(time.time, time.sleep)


def checkInSh(sc):
    checkIn()
    s.enter(540, 1, checkInSh, (sc,))


s.enter(540, 1, checkInSh, (s,))
s.run()
# checkin routine ====
