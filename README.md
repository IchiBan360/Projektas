# Zonemaster-cli-scan-tool
Įrankis automatizuoti darbą su zonemaster-cli domenų skenavimo įrankiu.

Pradėti naudotis įrankiu prireiks 2 bibliotekų:

Yagmail bibliotekos, kuri yra skirta palengvinti darbą su el. pašto siuntimu.

pip3 install yagmail[all]

ir DeepDiff bibliotekos, kuri yra skirta palengvinti darbą lyginant .json formato failus/

pip install deepdiff

Prieš paleidžiant skenavimo įrankį, geriausia būtų susikurti naują aplanką šiam įrankiui, ir į jį įdėti patį įrankį ir konfiguracinį failą.
Įrankis sukurs dvejus papildomus aplankus ir priklausant nuo testo tipo .json arba .txt tipo failą.
