import json
import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('workflows/**/*.json', recursive=True):
    if 'processar anexos' in f.lower():
        wf = json.load(open(f, encoding='utf-8'))
        print("Decidir download connections:")
        print(json.dumps(wf['connections'].get('Decidir download ou retorno seguro', {}), indent=2))
