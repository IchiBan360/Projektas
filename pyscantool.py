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

def klaiduPalyginimasTxt(domain):
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

def emailSiuntimas(body, files):

    print('siunciaum email')
    receivers = config['email-receivers']['receivers'].split(',') # nuskaitom gavejus
    for receiver in receivers: # nuskaitom gavejus is konfiguracijos failo
        yag = yagmail.SMTP('ichiban360@gmail.com', 'mhiwcixrszpuhjdz')
        yag.send(
                to=receiver,
                subject='Domenu skenavimo rezultatai',
                contents=body, # priklauso nuo lyginimo rezultatu
                attachments=files,
        )

# domenu testavimas TXT formatu
# iskvieciama zonemaster-cli funkcija, norint skenuoti nurodytus domenus
def skenavimasTxt(domain):

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

# Domenu skenavimas JSON formatu

def skenavimasJson(domain):

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

# Json testu rezultatu failu lyginimas

def klaiduPalyginimasJson(domain):
    if os.path.exists(testDirOld + domain + '.json'):
        with open(testDir + domain + '.json') as file_1, open(testDirOld + domain + '.json') as file_2:
            data1 = file_1.read()
            json_content_1 = json.loads(data1) # pakraunam abu json failus lyginimui
            data2 = file_2.read()
            json_content_2 = json.loads(data2)
            res = DeepDiff(json_content_2, json_content_1, ignore_string_type_changes = True, exclude_regex_paths="timestamp").to_json()
        return(res) # grazinama naujai atsiradusios klaidos 
    else:
        return('{}')


# sudedam visus domenu testu rezultatus i viena faila

def raportoFailasTxt():
    read_files = glob.glob(testDir + '/*.txt')
    with open (testOut, 'a') as outfile:
        for domain in domains:
            with open (testDir + domain + '.txt') as infile:
                outfile.write(infile.read())

def raportoFailasJson():
    read_files = glob.glob(testDir + '/*.json')
    errorList = {}
    for domain in domains:
        with open(testDir + domain + '.json', 'r') as infile:
            jsondiff = json.load(infile)
            errorList[domain +'_error'] = jsondiff
    
    with open(testOutJson, 'w') as outfile:
        json.dump(errorList, outfile, indent=4)


# tikrinam, ar buvo rasta nauju klaidu, ir siunciam el. pasta

def palyginimasTxt(diff):
    files=[testOut]
    if diff:
        emailSiuntimas(diff, files)
    else:
        diff = 'Domenu skenavimo metu nebuvo rasta nauju klaidu'
        emailSiuntimas(diff, files)


# kodo pradzia

print('dns skenavimo irankis \n')

cmd = 'zonemaster-cli' # zonemaster-cli komanda

# testo failu direktorijos

testOut = './testresult.txt'
testOutJson = './testresultJson.json'
testErrorJson = './testErrorJson.json'
configFilePath = './config.ini'
testDir = './testurezultatai/'
testDirOld = './testurezultataiseni/'

if not os.path.exists(configFilePath):
    print('nera konfiguracijos failo!')
    quit()

config = configparser.ConfigParser()
config.read(configFilePath) # skaitom konfiguracinio failo nustatymus

# Testavimo budo nuskaitymas is config.ini failo

sleepTime = config['sleep-time']['sleep']
tests = config['test-cases']['tests'].split(',')
domains = config['domain-names']['domains'].split(',')
poolCount = config['pool-count']['poolCount']
reportFormat = config['report-format']['format']

domainStr = ' '.join(map(str,domains))
testStr = ' '.join(map(str,tests))

if not os.path.exists(testDir):
    os.makedirs(testDir)
if not os.path.exists(testDirOld):
    os.makedirs(testDirOld)

if reportFormat == 'json': # Raporto kurimas JSON formatu

    while True:
        
        config = configparser.ConfigParser()
        config.read(configFilePath) # skaitom konfiguracinio failo nustatymus
        poolCount = config['pool-count']['poolCount']
        start_time = time.time()
        with Pool(processes=int(poolCount)) as pool: # parallel testu vykdymas
            pool.map(skenavimasJson, domains) # Pool kiekis priklauso nuo nurodyto kiekio
        print('uztruko %s sekundes' % (time.time() - start_time))
        raportoFailasJson() #Sudaromas raporto failas su visomis klaidomis
        errorlist = {} # susirasom visas naujas klaidas i zodyna
        for domain in domains:
            jsonResult = klaiduPalyginimasJson(domain)
            jsondiff = json.loads(jsonResult)
            if 'iterable_item_added' in jsondiff:
                errorlist[domain + '_error'] = jsondiff['iterable_item_added'] #Isirasom tik naujai rastas klaidas
        if errorlist.keys():
            print('buvo rasta nauju klaidu')
            fd = open(testErrorJson, 'w')
            json.dump(errorlist, fd, indent=4)
            fd.close()
            print('rasta nauju klaidu')
            body = ('Domenu skenavimo metu buvo rasta nauju klaidu!\n Skenuoti domenai: {} \n Daryti testai: {} \n \n Naujos klaidos pridetos testErrorJson faile'.format(domainStr,testStr))
            files=[testOutJson,testErrorJson]
        else:
            print('nerasta nauju klaidu')
            body = ('Domenu skenavimo metu nebuvo rasta nauju klaidu!\n Skenuoti domenai: {} \n Daryti testai: {}'.format(domainStr,testStr))
            files = [testOutJson]
        
        emailSiuntimas(body,files) # Siunciam email
        print('testavimus atlikau, laukiu ' + sleepTime + ' valandas/valandu')
        time.sleep(int(sleepTime) * 5) # sustabdom kodo vykdyma nurodytam laikotarpiui

elif reportFormat == 'txt': # Raporto kurimas TXT formatu

    fd = open(testOut, 'a') # irasom domenu ir testu pavadinimus
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
            pool.map(skenavimasTxt, domains) # Pool kiekis priklauso nuo nurodyto kiekio
        print('uztruko %s sekundes' % (time.time() - start_time))
        diff='' # susirasom naujai rastas klaidas i string kintamaji
        for domain in domains:
            diff += KlaiduPalyginimasTxt(domain)
        print (diff)
        palyginimasTxt(diff) # Tikrinam, ar buvo rasta nauju klaidu, nuo to pakeiciam el. pasto zinute
        print('testavimus atlikau, laukiu ' + sleepTime + ' valandas/valandu \n')
        time.sleep(int(sleepTime) * 3600) # sustabdom kodo vykdyma nurodytam laikotarpiui

else: # Suvedus bloga norima raporto formata niekas nebus daroma

    print('Nepasirinktas teisingas raporto failu formatas(json,txt)')
