"""Embed every synopsis in data.json with a local model (Ollama bge-m3). Output: embeddings.npy + embed_ids.json"""
import json, urllib.request, numpy as np
d = json.load(open('data.json'))
items = [('movie', m) for m in d['movies']] + [('tv', t) for t in d['tv_shows']]
items = [(t, it) for t, it in items if (it.get('overview') or '').strip()]
texts = [it['overview'].strip()[:2000] for _, it in items]
out = []
B = 32
for i in range(0, len(texts), B):
    req = urllib.request.Request('http://localhost:11434/api/embed',
        json.dumps({'model': 'bge-m3', 'input': texts[i:i+B], 'keep_alive': '5m'}).encode(),
        {'Content-Type': 'application/json'})
    out += json.load(urllib.request.urlopen(req, timeout=600))['embeddings']
    if i % 640 == 0: print(i, len(texts), flush=True)
urllib.request.urlopen(urllib.request.Request('http://localhost:11434/api/generate',
    json.dumps({'model': 'bge-m3', 'keep_alive': 0}).encode(), {'Content-Type': 'application/json'}))
np.save('embeddings.npy', np.array(out, dtype=np.float32))
json.dump([f"{t}:{it['id']}" for t, it in items], open('embed_ids.json', 'w'))
print('done', len(out))
