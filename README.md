# IPTC-annotate
Automatic annotation of JPEG images with IPTC data for keywords and caption/abstract using llava 1.6 running on ollama. 
## Install
Install [ollama](https://ollama.com/).
```
ollama pull llava:7b
python3 -m venv .venv
activate .venv
pip install -r requirements.txt
```
## Run
```
activate .venv
python iptc_annotate.py <directory>
```
## Command line options
```
-o | --overwrite -> Overwrite existing entries
-l | --language <ISO 936-1 code> -> Translate English into target language, not implememented yet.
```
## Config file iptc_annotate.conf
If not present, defaults are used:
```
[ollama]
model = llava:7b
base_URL = http://localhost:11434
timeout = 120
```
## Speed
On a Intel Core) i7-13700H, 32 GB, Nvidia RTX 2000 Ada, 8 GB, Windows 11 Pro x64: 4 seconds per image on average
