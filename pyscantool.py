import smtplib
import subprocess
import configparser
import os.path
import shutil
import time
import json
import fcntl
import requests
from difflib import Differ
from multiprocessing import Pool
from email.message import EmailMessage

# Raporto siuntimo elektroniniu pastu funkcija
# Visi el. pastai ir serveris yra nuskaitomi is konfiguracinio failo

def email(body, files):

    # Nuskaitom duomenis is konfiguracijos failo
    msg=EmailMessage() # el. pasto zinutes kurimas
    msg['subject']='Domenu skenavimo rezultatai'
    msg['from']=sender
    msg['to']=receivers
    msg.set_content(body)

    for f in files: # nuskaitom failus kuriuos siusime
        file_name=os.path.basename(f)
        with open(f) as file:
            file_data=file.read()
            msg.add_attachment(file_data, filename = file_name)

    if serverName: # Siuntimas per SMTP serveri, jei jis yra nurodytas
        try:
            with smtplib.SMTP_SSL(serverName) as server: # atidarome smtp serveri zinutes siuntimui
                server.ehlo()
                server.login(sender, password)
                server.send_message(msg)
                server.quit()
                print('\nel.pastas nusiustas sekmingai\n')
        except:
            print('\nNepavyko nusiusti el. pasto\n')
            exit(1)

    else: # Siuntimas per localhost SMTP serveri
        try:
            with smtplib.SMTP('localhost') as server:
                server.send_message(msg)
                server.quit()
                print('\nel.pastas nusiustas sekmingai\n')
        except:
            print('\nNepavyko nusiusti el. pasto\n')
            exit(1)

# domenu testavimas TXT formatu
# iskvieciama zonemaster-cli funkcija, norint skenuoti nurodytus domenus
def skenavimasTxt(domain):
    print('Tikrinamas domenas :', domain)
    if os.path.exists(os.path.join(testDir, domain + '.txt')): # perrasom senus domenu testu duomenis i faila
        shutil.copy(os.path.join(testDir, domain + '.txt'), testDirOld)
        os.remove(os.path.join(testDir, domain + '.txt'))
    fd = open(os.path.join(testDir, domain + '.txt'), 'a')
    fd.writelines(domain + '\n')
    fd.writelines('\n')
    fd.close()
    if len(tests) != 0:
        for test in tests: # vykdom visus nurodytus testus
            fd = open(os.path.join(testDir, domain + '.txt'), 'a')
            fd.writelines('testo tipas: ' + test + '\n')
            fd.close()
            fd = open(os.path.join(testDir, domain + '.txt'), 'a')
            subprocess.run([cmd, domain, '--test', test, '--no-time', '--level', 'notice'], stdout=fd) # zonemaster-cli funkcija
            fd.writelines('\n')
    else:
        fd = open(os.path.join(testDir, domain + '.txt'), 'a')
        fd.writelines('vykdomi visi testai \n')
        fd.close()
        fd = open(os.path.join(testDir, domain + '.txt'), 'a')
        subprocess.run([cmd, domain, '--no-time', '--level', 'notice'], stdout=fd) # zonemaster-cli funkcija
    fd.writelines('=======================================================\n')
    fd.writelines('\n')
    fd.close()

# Domenu skenavimas JSON formatu

def skenavimasJson(domain):

    print('Tikrinamas domenas :', domain)
    if os.path.exists(os.path.join(testDir, domain + '.json')): # perrasom senus domenu testu duomenis i faila
        shutil.copy(os.path.join(testDir, domain + '.json'), testDirOld)
        os.remove(os.path.join(testDir, domain + '.json'))
    fd = open(os.path.join(testDir, domain + '.json'), 'a')
    command = "{} {} --no-time --level notice --json".format(cmd, domain)
    if len(tests) != 0:
        for test in tests: # vykdom visus nurodytus testus
            command += " --test " + "{}".format(test)
        subprocess.run(command, stdout=fd, shell=True) # zonemaster-cli funkcija
    else:
        subprocess.run(command, stdout=fd, shell=True) # zonemaster-cli funkcija
    fd.close()

# Json testu rezultatu failu lyginimas

def klaiduPalyginimasJson(domain):
    erList = []
    # jei nera seno testo failo naujo turini perrasom i klaidas
    if not os.path.exists(os.path.join(testDirOld, domain + '.json')):
        with open(os.path.join(testDir, domain + '.json')) as fd:
            data = fd.read()
            json_content = json.loads(data)
            for errors in json_content:
                erList.append(errors)
    else: # Jei yra klaidu failas
        file_old = open(os.path.join(testDirOld, domain + '.json'))
        data_old = file_old.read()
        json_content_old = json.loads(data_old)
        with open(os.path.join(testDir, domain + '.json')) as fd:
            data = fd.read() # nusiskaitom rastas klaidas
            json_content = json.loads(data)
            for errors in json_content:
                matches = False
                arguments = errors['args']
                level = errors['level']
                tag = errors['tag']
                testcase = errors['testcase']
                errorList = [arguments, level, tag, testcase] # Isirasom tikrinamus dalykus i lista
                for errors_old in json_content_old:
                    arguments_old = errors_old['args']
                    level_old = errors_old['level']
                    tag_old = errors_old['tag']
                    testcase_old = errors_old['testcase'] # ta pati darom ir su senu failu
                    errorList_old = [arguments_old, level_old, tag_old, testcase_old]
                    if errorList == errorList_old: # jei radom vienoda klaida stabdom tikrinima, klaida jau buvo
                        matches = True
                        break
                if not matches: # Jei nebuvo klaidos, dedam ja i klaidu sarasa
                    erList.append(errors) 

    return erList # grazinamas klaidu sarasas

def klaiduPalyginimasTxt(domain):

    differences = ''
    count = 0
    if not os.path.exists(os.path.join(testDirOld, domain + '.txt')):
        file_1 = open(os.path.join(testDir, domain + '.txt'))
        for line in file_1.readlines():
            differences = differences + line
    else:
        file_2 = open(os.path.join(testDirOld, domain + '.txt'))
        with open(os.path.join(testDir, domain + '.txt')) as file_1:
            differ = Differ()
            for line in differ.compare(file_1.readlines(), file_2.readlines()):
                diff = line
                if diff.startswith('-'): # Tikrina, ar yra nauju skirtumu
                    count = count + 1
                    differences = differences + diff
        file_2.close()
    if count != 0:
        body = (domain + ' testo metu buvo rasta nauju klaidu: \n' + differences + '\n')
        return body
    else:
        return differences


# sudedam visus domenu testu rezultatus i viena faila

def raportoFailasTxt():
    with open (testOut, 'a') as outfile:
        for domain in domains: # Sudeda domenu atskiras ataskaitas i viena bendra
            with open (testDir + domain + '.txt') as infile:
                outfile.write(infile.read())

def raportoFailasJson():
    errorList = {}
    for domain in domains:
        with open(os.path.join(testDir, domain + '.json'), 'r') as infile:
            jsondiff = json.load(infile)
            errorList[domain] = jsondiff
    
    with open(testOutJson, 'w') as outfile: # Sudeda domenu atskiras ataskaitas i bendra json
        json.dump(errorList, outfile, indent=4)
        outfile.close()

# tikrinam, ar buvo rasta nauju klaidu, ir siunciam el. pasta

def palyginimasTxt(diff):
    files=[testOut]
    if diff: # Jei rasta klaidu
        body = 'Domenu skenavimo metu buvo rasta nauju klaidu!\n\nSkenuoti domenai: {} \n\nDaryti testai: {} \n\nNaujos klaidos: \n\n{} \n\nvisos klaidos pridetos testResult faile'.format(domainStr,testStr, diff)
        email(body, files)
    else: # Jei nerasta nauju klaidu
        if sendEmail:
            diff = 'Domenu skenavimo metu nebuvo rasta nauju klaidu!\n\nSkenuoti domenai: {} \n\nDaryti testai: {} \n\nSenos klaidos pridetos testResult faile'.format(domainStr,testStr)
            email(diff, files)
        else:
            print('\nEmail nesiunciamas\n')

#===================================
# kodo pradzia
#===================================

f = open ('lock', 'w') # Tikrinamas lock failas, jei jis yra atidarytas reiskia senas testas dar nebaigtas
try: fcntl.lockf (f, fcntl.LOCK_EX | fcntl.LOCK_NB)
except:
    print('[%s] Skenavimo irankis visdar atidarytas.\n' % time.strftime ('%c'))
    exit(1)

print('Domenu skenavimo irankis \n')

cmd = 'zonemaster-cli' # zonemaster-cli komanda

# testo failu direktorijos

homeDir = os.path.expanduser('~') # Naudotojo namu direktorijos gavimas
configFilePaths =['/etc/pyscantool/config.ini', os.path.join(homeDir, '/pyscantool/config.ini'),
                  os.path.join(homeDir, '/config.ini'), 'config.ini']
for cPath in configFilePaths:
    if os.path.exists(cPath): # Tikrinama, ar egzistuoja konfiguracijos failas
        confdir = cPath
        config = configparser.ConfigParser()
        config.read(cPath)
        break

if not 'config' in globals(): # Jei konfiguracijos failas neegzistuoja, nutraukiamas darbas
    print('nera konfiguracijos failo!')
    exit(1)

# El. pasto siuntimui reikalingu parametru nuskaitymas

receivers = config.get('email-parameters', 'receivers', fallback='')
receivers = [x for x in receivers.split(',') if x != ''] 
serverName = config.get('email-parameters', 'server', fallback='')
sender = config.get('email-parameters', 'sender', fallback='')
password = config.get('email-parameters', 'password', fallback= '')

if len(receivers) == 0 and not sender: # Tikrinama, ar yra yrasyti gavejai ir siuntejas
    print('Nenurodyta gavejai arba siuntejas!')
    exit(1)

if serverName:
    if not password: # Ivedus serveri, tikrinama, ar yra ivestas slaptazodis
        print ('Naudojant smtp serveri privaloma irasyti slaptazodi!')
        exit(1)

# Skenavimui reikalingu parametru nuskaitymas is config.ini failo

tests = config.get('test-parameters', 'tests', fallback='')
tests = [ x for x in tests.split(',') if x != '']
poolCount = config.get('test-parameters', 'poolcount', fallback=8) 
reportFormat = config.get('report-parameters', 'format', fallback='json')
reportDir = config.get('report-parameters', 'directory', fallback= '')
url = config.get('test-parameters', 'url'.strip('\n'), fallback='')
sendEmail = config.getboolean('report-parameters', 'report-no-diff', fallback=True)

# Failu direktorijos

testOut = os.path.join(reportDir, 'testResult.txt') # txt raporto direktorija
testOutJson = os.path.join(reportDir, 'testResultJson.json') # json raporto direktorija
testErrorJson = os.path.join(reportDir, 'testErrorJson.json') # json nauju klaidu failo direktorija
testDir = os.path.join(reportDir, 'testuRezultatai/') # domenu klaidu raporto direktorija
testDirOld = os.path.join(reportDir, 'testuRezultataiSeni/') # domeun senu klaidu raporto direktorija

# Domenu saraso parsisiuntimas is interneto
# ir duomenu nuskaitymas

if url:
    domainFile = requests.get(url)
    if domainFile.status_code != 200: # tikrinam, ar domenu failas yra pasiekiamas
        print('Domenu failas nepasiekiamas, {} klaida'.format(domainFile.status_code))
        exit(1)
else:
    print('Domenu failu url nenurodytas config.ini faile!')
    exit(1)

open('domainFile.txt', 'wb').write(domainFile.content) # Irasom domenus i lokalu faila
with open ('domainFile.txt') as f:
    domains = [x for x in f.read().splitlines() if x != '']

if len(domains) == 0: # Tikrinam, ar faile isvis yra domenu
    print('Domenų sąrašas tuščias!')
    exit(1)

domainStr = ' '.join(map(str,domains))
testStr = ' '.join(map(str,tests))
if not testStr: # Tikrinam, ar yra nurodyti testai config.ini faile
    testStr = 'Visi testai'

if not os.path.exists(testDir): # Tikrinam ar egzistuoja testu direktorijos
    os.makedirs(testDir)
if not os.path.exists(testDirOld):
    os.makedirs(testDirOld)

errorString = ''
if reportFormat == 'json': # Raporto kurimas JSON formatu
    
    start_time = time.time()
    with Pool(processes=int(poolCount)) as pool: # parallel testu vykdymas
        pool.map(skenavimasJson, domains) # Pool kiekis priklauso nuo nurodyto kiekio
    print('\nUztruko %.2f sekundes' % (time.time() - start_time))

    raportoFailasJson() #Sudaromas raporto failas su visomis klaidomis
    errorlist = {} # susirasom visas naujas klaidas i zodyna
    
    for domain in domains:
        jsonDiff = klaiduPalyginimasJson(domain) # Senu ir nauju domenu skenavimo rezulatu lyginimas
        if jsonDiff:
            errorlist[domain] = jsonDiff
            errorString += '\n' + domain + ' domeno klaidos: \n'
            for entry in errorlist[domain]: # Klaidu sarasas el. pasto siuntimui      
                errorString += '''
                args {}
                Level: {} 
                Module: {} 
                Tag: {} 
                TestCase: {} 
                '''.format(entry['args'], entry['level'], entry['module']
                ,entry['tag'], entry['testcase'])
    if  errorlist: # Jei buvo rasta nauju klaidu
        fd = open(testErrorJson, 'w')
        json.dump(errorlist, fd, indent=4)
        fd.close()
        print('\nRasta nauju klaidu')
        body = ('Domenu skenavimo metu buvo rasta nauju klaidu!\n\nSkenuoti domenai: {} \n\nDaryti testai: {} \n\nNaujos klaidos: \n\n{} \n\nNaujos klaidos pridetos testErrorJson faile, visos klaidos yra testResultJson faile'.format(domainStr,testStr, errorString))
        files=[testOutJson,testErrorJson]
        email(body,files) # el. pasto siuntimas
    else: # Jei nebuvo rasta nauju klaidu
        print('\nNerasta nauju klaidu')
        if sendEmail: # Tikrinam, ar reikiu siusti el. pasta
            body = ('Domenu skenavimo metu nebuvo rasta nauju klaidu!\n\nSkenuoti domenai: {} \n\nDaryti testai: {} \n\nSenos klaidos pridetos testResultJson faile'.format(domainStr,testStr))
            files = [testOutJson]
            email(body,files)
        else:
            print('\nEmail nesiunciamas')
    print('\nTestavimas atliktas sekmingai')
    exit(0)

elif reportFormat == 'txt': # Raporto kurimas TXT formatu

    fd = open(testOut, 'w') # irasom domenu ir testu pavadinimus
    fd.writelines('Testuojami domenai: ' + domainStr + '\n')
    fd.writelines('\n')
    fd.writelines('Testu tipai: ' + testStr + '\n')
    fd.writelines('\n')
    fd.close()
  
    start_time = time.time()
    with Pool(processes=int(poolCount)) as pool: # parallel testu vykdymas
        pool.map(skenavimasTxt, domains) # Pool kiekis priklauso nuo nurodyto kiekio
    print('\nUztruko %.2f sekundes' % (time.time() - start_time))
    raportoFailasTxt()
    diff='' # susirasom naujai rastas klaidas i string kintamaji
    for domain in domains:
        diff += klaiduPalyginimasTxt(domain)
    palyginimasTxt(diff) # Tikrinam, ar buvo rasta nauju klaidu, nuo to pakeiciam el. pasto zinute
    print('\nTestavimas atliktas sekmingai')
    exit(0)

else: # Suvedus bloga norima raporto formata niekas nebus daroma

    print('Nepasirinktas teisingas raporto failu formatas(json,txt)')
    exit(1)
