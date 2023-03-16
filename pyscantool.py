import smtplib
import subprocess
import configparser
import os.path
import shutil
import time
import glob
import json
import fcntl
import requests
from difflib import Differ
from deepdiff import DeepDiff
from multiprocessing import Pool
from email.message import EmailMessage

# Raporto siuntimo elektroniniu pastu funkcija
# Visi el. pastai ir serveris yra nuskaitomi is konfiguracinio failo

def email(body, files):
    # Nuskaitom duomenis is konfiguracijos failo
    receivers = config['email-parameters']['receivers'].split(',') 
    serverName = config['email-parameters']['server']
    sender = config['email-parameters']['sender']
    password = config['email-parameters']['password']
    msg=EmailMessage() # el. pasto zinutes kurimas
    msg['subject']='Domenu skenavimo rezultatai'
    msg['from']=sender
    msg['to']=receivers
    msg.set_content(body)

    for f in files: # nuskaitom failus kuriuos siusime
        with open(f) as file:
            file_data=file.read()
            file_name=file.name
            msg.add_attachment(file_data,filename=file_name)

    if serverName:
        if not sender or not password or receivers == ['']:
            print('Nenurodyta reikalaujami duomenys el. pasto siuntimui')
            exit(1)
        else: 
            try:
                with smtplib.SMTP_SSL(serverName) as server: # atidarome smtp serveri zinutes siuntimui
                    server.ehlo()
                    server.login(sender, password)
                    #server.send_message(msg)
                    server.quit()
            except:
                print('Nepavyko nusiusti el. pasto')
                exit(1)

    else:
        if not sender or receivers == ['']:
            print ('Nenurodyta reikalaujami duomenys el. pasto siuntimui')
            exit(1)
        else:
            try:
                with smtplib.SMTP('localhost') as server:
                    #server.send_message(msg)
                    server.quit()
            except:
                print('Nepavyko nusiusti el. pasto')
                exit(1)


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
    if tests != ['']:
        for test in tests: # vykdom visus nurodytus testus
            fd = open(testDir + domain + '.txt', 'a')
            fd.writelines('testo tipas: ' + test + '\n')
            fd.close()
            fd = open(testDir + domain + '.txt', 'a')
            subprocess.run([cmd, domain, '--test', test, '--no-time', '--level', 'notice'], stdout=fd) # zonemaster-cli funkcija
            fd.writelines('\n')
    else:
        fd = open(testDir + domain + '.txt', 'a')
        fd.writelines('vykdomi visi testai \n')
        fd.close()
        fd = open(testDir + domain + '.txt', 'a')
        subprocess.run([cmd, domain, '--no-time', '--level', 'notice'], stdout=fd) # zonemaster-cli funkcija
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
    if tests != ['']:
        for test in tests: # vykdom visus nurodytus testus
            command += " --test " + "{}".format(test)
        subprocess.run(command, stdout=fd, shell=True) # zonemaster-cli funkcija
    else:
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
            res = DeepDiff(json_content_2, json_content_1, exclude_paths='timestamp').to_json()
        return(res)
    else:
        return('{}')


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
    else:
        return ''

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
            errorList[domain] = jsondiff
    
    with open(testOutJson, 'w') as outfile:
        json.dump(errorList, outfile, indent=4)


# tikrinam, ar buvo rasta nauju klaidu, ir siunciam el. pasta

def palyginimasTxt(diff):
    files=[testOut]
    if diff:
        email(diff, files)
    else:
        diff = 'Domenu skenavimo metu nebuvo rasta nauju klaidu'
        email(diff, files)

#==================================
# kodo pradzia
#==================================

f = open ('lock', 'w')
try: fcntl.lockf (f, fcntl.LOCK_EX | fcntl.LOCK_NB)
except:
    print('[%s] Skenavimo irankis visdar atidarytas.\n' % time.strftime ('%c'))
    exit(1)

print('dns skenavimo irankis \n')

cmd = 'zonemaster-cli' # zonemaster-cli komanda

# testo failu direktorijos

homeDir = os.path.expanduser('~')
configFilePaths =['/etc/pyscantool/config.ini', os.path.join(homeDir + '/pyscantool/config.ini'),
                  os.path.join(homeDir + '/config.ini'), 'config.ini']
for cPath in configFilePaths:
    if os.path.exists(cPath):
        config = configparser.ConfigParser()
        config.read(cPath)
        break

if not 'config' in globals():
    print('nera konfiguracijos failo!')
    exit(1)



# Testavimo budo nuskaitymas is config.ini failo

tests = config['test-parameters']['tests'].split(',')
poolCount = config['test-parameters']['poolCount']
reportFormat = config['report-parameters']['format']
reportDir = config['report-parameters']['directory']
url = config['test-parameters']['url'].strip('\n')

if not poolCount: # jei nebus nurodyta pool kiekio, default padarom 4
    poolCount = 4

# Failu direktorijos

testOut = os.path.join(reportDir +'testresult.txt')
testOutJson = os.path.join(reportDir +'testresultJson.json')
testErrorJson = os.path.join(reportDir +'testErrorJson.json')
testDir = os.path.join(reportDir +'testurezultatai/')
testDirOld = os.path.join(reportDir +'testurezultataiseni/')

# Domenu saraso parsisiuntimas is interneto
# ir duomenu nuskaitymas

domainFile = requests.get(url)

if domainFile.status_code != 200: # tikrinam, ar domenu failas yra pasiekiamas
    print('Domenu failas nepasiekiamas, {} klaida'.format(domainFile.status_code))
    exit(1)

open('domainFile.txt', 'wb').write(domainFile.content) # Irasom domenus i lokalu faila
with open ('domainFile.txt') as f:
    domains = f.read().splitlines()

if domains == ['']: # Tikrinam, ar faile isvis yra domenu
    print('Domenų sąrašas tuščias!')
    exit(1)

domainStr = ' '.join(map(str,domains))
testStr = ' '.join(map(str,tests))

if not os.path.exists(testDir): # Tikrinam ar egzistuoja testu direktorijos
    os.makedirs(testDir)
if not os.path.exists(testDirOld):
    os.makedirs(testDirOld)
errorString = ''
if reportFormat == 'json': # Raporto kurimas JSON formatu
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
            errorlist[domain] = jsondiff['iterable_item_added'] #Isirasom tik naujai rastas klaidas
            errorString += '\n' + domain + ' domeno klaidos: \n'
            for key in errorlist[domain].keys():
                errorString += '''
                Level: {} 
                Module: {} 
                Tag: {} 
                TestCase: {} 
                '''.format(errorlist[domain][key]['level'], errorlist[domain][key]['module']
                            ,errorlist[domain][key]['tag'], errorlist[domain][key]['testcase'])
    if errorlist.keys():
        print('buvo rasta nauju klaidu')
        fd = open(testErrorJson, 'w')
        json.dump(errorlist, fd, indent=4)
        fd.close()
        print('rasta nauju klaidu')
        body = ('Domenu skenavimo metu buvo rasta nauju klaidu!\n\nSkenuoti domenai: {} \n\nDaryti testai: {} \n\nNaujos klaidos: \n\n{} \n\nNaujos klaidos pridetos testErrorJson faile'.format(domainStr,testStr, errorString))
        files=[testOutJson,testErrorJson]
    else:
        print('nerasta nauju klaidu')
        body = ('Domenu skenavimo metu nebuvo rasta nauju klaidu!\n\nSkenuoti domenai: {} \n\nDaryti testai: {}'.format(domainStr,testStr))
        files = [testOutJson]
    email(body,files)
    print('\ntestavimas atliktas sekmingai')
    exit(0)

elif reportFormat == 'txt': # Raporto kurimas TXT formatu

    fd = open(testOut, 'a') # irasom domenu ir testu pavadinimus
    fd.writelines('Testuojami domenai: ' + domainStr + '\n')
    fd.writelines('\n')
    fd.writelines('Testu tipai: ' + testStr + '\n')
    fd.writelines('\n')
    fd.close()
  
    start_time = time.time()
    with Pool(processes=int(poolCount)) as pool: # parallel testu vykdymas
        pool.map(skenavimasTxt, domains) # Pool kiekis priklauso nuo nurodyto kiekio
    print('uztruko %s sekundes' % (time.time() - start_time))
    raportoFailasTxt()
    diff='' # susirasom naujai rastas klaidas i string kintamaji
    for domain in domains:
        diff += klaiduPalyginimasTxt(domain)
    print (diff)
    palyginimasTxt(diff) # Tikrinam, ar buvo rasta nauju klaidu, nuo to pakeiciam el. pasto zinute
    print('testavimas atliktas sekmingai')
    exit(0)

else: # Suvedus bloga norima raporto formata niekas nebus daroma

    print('Nepasirinktas teisingas raporto failu formatas(json,txt)')
    exit(1)
