import subprocess
import configparser
import os.path
import shutil
import sys
import yagmail
from difflib import Differ


def palyginimas():
    with open(testOut) as file_1, open (testOld) as file_2:
        differences = ''
        if file_1.readline() != file_2.readline():
            print('scenuojami nauji domentai')
            body = 'Skenavimo metu naudota nauji dometai'
            emailSiuntimas(body)
        elif file_1.readline() != file_2.readline():
            print('naudojami nauji testai')
            body = 'Skenavimo metu naudota nauji testavimo budai'
       #     emailSiuntimas(body)
       # else:
            print('domenai ir testcase vienodi')
            differ = Differ()
            for line in differ.compare(file_1.readlines(), file_2.readlines()):
                diff = line
                if diff.startswith('-'):
                    differences = 'Rastos naujos klaidos!\n'
                    differences = differences + diff
    print(differences)
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

print('dns scenavimo irankis')

cmd = 'zonemaster-cli' # zonemaster-cli komanda

# testo failu direktorijos

config = configparser.ConfigParser()
testOut = './testresult.txt'
configFilePath = './config.ini'
testOld = './testresultold.txt'

# Tikrinam ar egzistuoja testo rezultatu failas
# Jei egzistuoja, kopijuojam i sena testu faila

if os.path.exists(testOut):
    print('testas jau buvo darytas')
    shutil.copyfile(testOut, testOld)
    os.remove(testOut)

#Testavimo budo nuskaitymas is config.ini failo

config.read(configFilePath) # skaitom konfiguracinio failo nustatymus
tests = config['test-cases']['tests'].split(',')
domains = config['domain-names']['domains'].split(',')
fd = open(testOut, 'a') # irasom domenu ir testu pavadinimus
domainStr = ' '.join(map(str,domains))
testStr = ' '.join(map(str,tests))
fd.writelines('Lyginami domenai: ' + domainStr + '\n')
fd.writelines('Naudojami testai: ' + testStr + '\n')
fd.close()

# domenu testavimas

for domain in domains: # einam per visus nurodytus domenus
    print('Tikrinamas domenas :', domain) 
    fd = open(testOut, 'a')
    fd.writelines(domain + '\n')
    fd.close()
    for test in tests: # vykdom visus nurodytus testus
        fd = open(testOut, 'a') 
        fd.writelines('testo tipas: ' + test + '\n')
        fd.close()
        fd = open(testOut, 'a')
        subprocess.run([cmd, domain, '--test', test, '--no-time'], stdout=fd) # zonemaster-cli funkcija
        fd.writelines('\n')
        fd.close()

# lyginam nauja ir sena testu faila
# jei naudojami nauji domenai arba testai
# failu nelyginam, nes jie taip ar taip bus skirtingi

palyginimas() # lyginam 2 failus ieskant nauju klaidu


