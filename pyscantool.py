import subprocess
import configparser
import os.path
import shutil
import filecmp
import sys
import yagmail

print('dns scenavimo irankis')

cmd = 'zonemaster-cli'

config = configparser.ConfigParser()
testOut = './testresult.txt'
configFilePath = './config.ini'
testOld = './testresultold.txt'
#Tikrinam ar egzistuoja testo rezultatu failas
#Jei egzistuoja, kopijuojam i sena testu faila
if os.path.exists(testOut):
    print('testas jau buvo darytas')
    shutil.copyfile(testOut, testOld)
    os.remove(testOut)

#Testavimo budo nuskaitymas is config.ini failo
config.read(configFilePath)
tests = config['test-cases']['tests'].split(',')
print('Pasirinktas skenavimo budas:',tests)

domains = config['domain-names']['domains'].split(',')
for domain in domains:
    print('Tikrinamas domenas :', domain)
    fd = open(testOut, 'a')
    fd.writelines(domain + '\n')
    fd.close()
    for test in tests:
        fd = open(testOut, 'a')
        subprocess.run([cmd, domain, '--test', test], stdout=fd)
        fd.writelines('\n')
        fd.close()

if filecmp.cmp(testOut, testOld):
    body = 'Nauju klaidu nerasta'
    print('nauju klaidu nerasta')
else:
    body = 'Rasta nauju klaidu!'

#kolkas uzkomentuoju kad kaskart email nesiustu
print('siunciaum email')
receivers = config['email-receivers']['receivers'].split(',')
for receiver in receivers:
    yag = yagmail.SMTP('ichiban360@gmail.com', 'mhiwcixrszpuhjdz')
    yag.send(
            to=receiver,
            subject='Domenu skenavimo rezultatai',
            contents=body,
            attachments=testOut,
    )
