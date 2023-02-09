import subprocess
import configparser


print('dns scenavimo irankis')

cmd = 'zonemaster-cli' 

config = configparser.ConfigParser()
configFilePath = '/home/karolis/projektas/config.ini'

config.read(configFilePath)

test = config['pyscantool-config']['testcase']
print('Pasirinktas skenavimo budas:',test)  
temp = subprocess.Popen([cmd,'domreg.eu --test' + test])
