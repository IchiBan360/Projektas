import subprocess
import configparser
import os.path
import shutil
import difflib
import sys

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
test = config['test-case']['testcase']
print('Pasirinktas skenavimo budas:',test)

domains = config['domain-names']['domains'].split(',')
for domain in domains:
    print('Tikrinamas domenas :', domain)
    fd = open(testOut, 'a')
    fd.writelines(domain + '\n')
    fd.close()
    fd = open(testOut, 'a')
    subprocess.run([cmd, domain, '--test', test], stdout=fd)
    fd.writelines('\n')
    fd.close()

with open(testOut, 'r') as f1:
    with open(testOld, 'r') as f2:
        diff = difflib.unified_diff(
                f1.readlines(),
                f2.readlines(),
                fromfile='f1',
                tofile='f2',
        )
        for line in diff:
            print(line)


# closing files
f1.close()                                      
f2.close()  
