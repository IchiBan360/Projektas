# Zonemaster-cli-scan-tool
Įrankis automatizuoti darbą su zonemaster-cli domenų skenavimo įrankiu.

Pradėti naudotis įrankiu prireiks Zonemaster-cli bibliotekos, skirtos skenuoti nurodytus domenus:

curl -LOs https://package.zonemaster.net/setup.sh

sudo sh setup.sh

sudo apt install zonemaster-cli

Prieš paleidžiant skenavimo įrankį, geriausia būtų susikurti naują aplanką šiam įrankiui, ir į jį įdėti patį įrankį ir konfiguracinį failą.
Įrankis sukurs dvejus papildomus aplankus ir priklausant nuo testo tipo .json arba .txt tipo failą.
