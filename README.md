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
python iptc_annotate.py <directory>
```
