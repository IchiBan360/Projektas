import subprocess
import configparser
import os.path
import shutil
import sys
import yagmail
import time
import glob
from difflib import Differ



def palyginimas(domain):
    differences = ''
    count = 0
    with open(testDir + domain + '.txt') as file_1, open(testDirOld + domain + '.txt') as file_2:
        differ = Differ()
        for line in differ.compare(file_1.readlines(), file_2.readlines()):
            diff = line
            if diff.startswith('-'):
                count = count + 1
                differences = differences + diff
    if count != 0:
        body = (domain + ' testo metu buvo rasta nauju klaidu::\n' + differences)
        return body
    else:
        return ''
        print('nauju klaidu nerasta')
    
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

def testavimas():
    if os.path.exists(testOut):
        print('testas jau buvo darytas')
        shutil.copyfile(testOut, testOld)
        os.remove(testOut)

#Testavimo budo nuskaitymas is config.ini failo

#    config.read(configFilePath) # skaitom konfiguracinio failo nustatymus
    tests = config['test-cases']['tests'].split(',')
    domains = config['domain-names']['domains'].split(',')
    fd = open(testOut, 'a') # irasom domenu ir testu pavadinimus
    domainStr = ' '.join(map(str,domains))
    testStr = ' '.join(map(str,tests))
    fd.writelines('Testuojami domenai: ' + domainStr + '\n')
    fd.writelines('\n')
    fd.writelines('Testu tipai: ' + testStr + '\n')
    fd.writelines('\n')
    fd.close()

# domenu testavimas
    diff = ''
    for domain in domains: # einam per visus nurodytus domenus
        print('Tikrinamas domenas :', domain)
        if os.path.exists(testDir + domain + '.txt'):
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
            subprocess.run([cmd, domain, '--test', test, '--no-time'], stdout=fd) # zonemaster-cli funkcija
            fd.writelines('\n')
        fd.writelines('=======================================================\n')
        fd.writelines('\n')
        fd.close()
        diff += palyginimas(domain)
    print (diff)
    
    read_files = glob.glob(testDir + '/*.txt')
    with open (testOut, 'wb') as outfile:
        for f in read_files:
            with open(f, 'rb') as infile:
                outfile.write(infile.read())

# lyginam nauja ir sena testu faila
# jei naudojami nauji domenai arba testai
# failu nelyginam, nes jie taip ar taip bus skirtingi

  #  palyginimas() # lyginam 2 failus ieskant nauju klaidu

print('dns scenavimo irankis')

cmd = 'zonemaster-cli' # zonemaster-cli komanda

# testo failu direktorijos

#config = configparser.ConfigParser()
#config.read(configFilePath) # skaitom konfiguracinio failo nustatymus
testOut = './testresult.txt'
configFilePath = './config.ini'
testOld = './testresultold.txt'
testDir = './testurezultatai/'
testDirOld = './testurezultataiseni/'

config = configparser.ConfigParser()
config.read(configFilePath) # skaitom konfiguracinio failo nustatymus

sleepTime = config['sleep-time']['sleep']



#while True:
testavimas()
print('testavimus atlikau, laukiu 60 sekundziu')
    #time.sleep(int(sleepTime) * 3600)

