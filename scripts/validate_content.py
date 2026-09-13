import json
from pathlib import Path
d=json.loads(Path('content/episodes.json').read_text(encoding='utf-8'))
req=['chapter','deity','title','text','label','image','textPosition']
for i,e in enumerate(d.get('episodes',[]),1):
    missing=[k for k in req if not e.get(k)]
    if missing: raise ValueError(f'Episode {i}: missing {missing}')
print(f"OK — {len(d.get('episodes',[]))} episodes validated.")
