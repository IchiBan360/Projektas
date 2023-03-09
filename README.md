# Zonemaster-cli-scan-tool
Įrankis automatizuoti darbą su zonemaster-cli domenų skenavimo įrankiu.

Pradėti naudotis įrankiu prireiks 2 bibliotekų:

Zonemaster-cli biblioteka, skirta skenuoti nurodytus domenus:

curl -LOs https://package.zonemaster.net/setup.sh

sudo sh setup.sh

sudo apt install zonemaster-cli

ir DeepDiff bibliotekos, kuri yra skirta palengvinti darbą lyginant .json formato failus:

pip install deepdiff

Prieš paleidžiant skenavimo įrankį, geriausia būtų susikurti naują aplanką šiam įrankiui, ir į jį įdėti patį įrankį ir konfiguracinį failą.
Įrankis sukurs dvejus papildomus aplankus ir priklausant nuo testo tipo .json arba .txt tipo failą.
