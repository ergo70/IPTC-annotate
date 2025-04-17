# IPTC-annotate
Automatic recursive annotation of JPEG images with IPTC data for five keywords and a caption/abstract, using llava 1.6 running on ollama. Requires Python >= 3.7.x.
## Install
Install [ollama](https://ollama.com/).
```
ollama pull llava:7b
python3 -m venv .venv
activate .venv
pip install -r requirements.txt
```
## Run
Annotate all JPEG images in `<directory>` and its subdirectories.
```
activate .venv
python iptc_annotate.py <directory>
```
## Command line options
```
-o | --overwrite -> Overwrite existing entries
-l | --language <ISO 936-1 code> -> Translate English into target language. Not implememented yet.
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
On a Intel Core) i7-13700H, 32 GB, Nvidia RTX 2000 Ada, 8 GB, Windows 11 Pro x64: About 4 seconds per image with the llava:7b model. Larger models slow down annotation without noticeable improvement in annotation quality.

## Caveats
caption/abstract is written and can be read back by IPTCInfo3, yet it is not visible e.g. with CaptureOne in images coming from a Canon Powershot G12 (2010-2012). Reason unknown, probably changes in the IPTC specification after the Powershot G12 was discontinued in 2012 or some issue of IPTCInfo3. IPhone and Android photos behave as expected.
