import subprocess
import configparser
import os.path
import shutil
import sys
import yagmail
import time
import glob
import json
from difflib import Differ
from deepdiff import DeepDiff
from multiprocessing import Pool

# patikrina, ar naujam domeno testo faile yra nauju klaidu
# jei taip, sudeda visas rastas naujas klaidas i bendra body
# el. pasto siuntimui

def palyginimas(domain):
    differences = ''

    count = 0
    if os.path.exists(testDirOld + domain + '.txt'):
        with open(testDir + domain + '.txt') as file_1, open(testDirOld + domain + '.txt') as file_2:
            differ = Differ()
            for line in differ.compare(file_1.readlines(), file_2.readlines()):
                diff = line
                if diff.startswith('-'):
                    count = count + 1
                    differences = differences + diff
        if count != 0:
            body = (domain + ' testo metu buvo rasta nauju klaidu: \n' + differences)
            return body
        else:
            return differences
            print('nauju klaidu nerasta')
    else:
        return ''
    
# email raporto siuntimo metodas
# siuncia domenu skenavimo rezultatus visiems nurodytiems adresatams

def emailSiuntimas(body):

    print('siunciaum email')
    receivers = config['email-receivers']['receivers'].split(',') # nuskaitom gavejus
    for receiver in receivers: # nuskaitom gavejus is konfiguracijos failo
        yag = yagmail.SMTP('ichiban360@gmail.com', 'mhiwcixrszpuhjdz')
        yag.send(
                to=receiver,
                subject='Domenu skenavimo rezultatai',
                contents=body, # priklauso nuo lyginimo rezultatu
                attachments=testOut,
        )

# tikrinam, ar egzistuoja raporto failas, jei taip keiciam su atliktu raportu

def failoKurimas():
    if os.path.exists(testOut):
        shutil.copyfile(testOut, testOld)
        os.remove(testOut)


# domenu testavimas

def testavimas(domain):

    print('Tikrinamas domenas :', domain)
    if os.path.exists(testDir + domain + '.txt'): # perrasom senus domenu testu duomenis i faila
        shutil.copy(testDir + domain + '.txt', testDirOld)
        os.remove(testDir + domain + '.txt')
    fd = open(testDir + domain + '.txt', 'a')
    fd.writelines(domain + '\n')
    fd.writelines('\n')
    fd.close()
    for test in tests: # vykdom visus nurodytus testus
        fd = open(testDir + domain + '.txt', 'a')
        fd.writelines('testo tipas: ' + test + '\n')
        fd.close()
        fd = open(testDir + domain + '.txt', 'a')
        subprocess.run([cmd, domain, '--test', test, '--no-time', '--level', 'notice'], stdout=fd) # zonemaster-cli funkcija
        fd.writelines('\n')
    fd.writelines('=======================================================\n')
    fd.writelines('\n')
    fd.close()

def testavimasJson(domain):

    print('Tikrinamas domenas :', domain)
    if os.path.exists(testDir + domain + '.json'): # perrasom senus domenu testu duomenis i faila
        shutil.copy(testDir + domain + '.json', testDirOld)
        os.remove(testDir + domain + '.json')
    fd = open(testDir + domain + '.json', 'a')
    command = "{} {} --no-time --level notice --json".format(cmd, domain)
    for test in tests: # vykdom visus nurodytus testus
        command += " --test " + "{}".format(test)
    subprocess.run(command, stdout=fd, shell=True) # zonemaster-cli funkcija
    fd.close()


def jsonTikrinimas(domain):
    
    with open(testDir + domain + '.json') as json_file:
        data = json_file.read()
        json_content = json.loads(data)
        print(domain + ' domeno rastos klaidos')
        #print(json.dumps(json_content, indent=4))
        #for level in json_content:
        #   print(level['level'], level['module'], level['tag'], level['testcase'])

def jsonPalyginimas():
    result = ''
    for domain in domains:
        if os.path.exists(testDirOld + domain + '.json'):
            with open(testDir + domain + '.json') as file_1, open(testDirOld + domain + '.json') as file_2:
                data1 = file_1.read()
                json_content_1 = json.loads(data1)
                data2 = file_2.read()
                json_content_2 = json.loads(data2)
                res = (str(DeepDiff(json_content_1, json_content_2, exclude_regex_paths="timestamp")))
                if res == '{}': #TODO pasidaryk normalu lyginima pagaliau
                    print('jokiu pakeitimu')
                else:
                    result += res 
    return(result)



# sudedam visus domenu testu rezultatus i viena faila

def raportoFailas():
    read_files = glob.glob(testDir + '/*.txt')
    with open (testOut, 'a') as outfile:
        for domain in domains:
            with open (testDir + domain + '.txt') as infile:
                outfile.write(infile.read())

# tikrinam, ar buvo rasta nauju klaidu, ir siunciam el. pasta

def skirtumuLyginimas(diff):
    if diff:
    #    emailSiuntimas(diff)
        print('yra nauju klaidu' + diff)
    else:
        diff = 'Domenu skenavimo metu nebuvo rasta nauju klaidu'
     #   emailSiuntimas(diff)
        print(diff)

# kodo pradzia

print('dns scenavimo irankis')

cmd = 'zonemaster-cli' # zonemaster-cli komanda

# testo failu direktorijos

testOut = './testresult.txt'
testOutJson = './testresultJson.txt'
configFilePath = './config.ini'
testOld = './testresultold.txt'
testOldJson = './testresultoldJson.txt'
testDir = './testurezultatai/'
testDirOld = './testurezultataiseni/'

config = configparser.ConfigParser()
config.read(configFilePath) # skaitom konfiguracinio failo nustatymus

sleepTime = config['sleep-time']['sleep']

if os.path.exists(testOut):
    shutil.copyfile(testOut, testOld)
    os.remove(testOut)

# Testavimo budo nuskaitymas is config.ini failo

tests = config['test-cases']['tests'].split(',')
domains = config['domain-names']['domains'].split(',')
poolCount = config['pool-count']['poolCount']
fd = open(testOut, 'a') # irasom domenu ir testu pavadinimus
domainStr = ' '.join(map(str,domains))
testStr = ' '.join(map(str,tests))
fd.writelines('Testuojami domenai: ' + domainStr + '\n')
fd.writelines('\n')
fd.writelines('Testu tipai: ' + testStr + '\n')
fd.writelines('\n')
fd.close()

while True: # paprastas loop kartoti testams kas kazkiek laiko
    config = configparser.ConfigParser()
    config.read(configFilePath) # skaitom konfiguracinio failo nustatymus
    poolCount = config['pool-count']['poolCount']
    start_time = time.time()
    with Pool(processes=int(poolCount)) as pool: # parallel testu vykdymas
        pool.map(testavimasJson, domains) # Pool kiekis priklauso nuo domenu kiekio
    print('uztruko %s sekundes' % (time.time() - start_time))
    print(jsonPalyginimas())
    #raportoFailas()
    #diff=''
    #for domain in domains:
    #    diff += palyginimas(domain)
    #print (diff)
    #skirtumuLyginimas(diff)
    print('testavimus atlikau, laukiu ' + sleepTime + ' valandas/valandu')
    time.sleep(int(sleepTime) * 5)
