"""Keep themes.json in step with data.json. Only NEW titles are read by the local model (Ollama bge-m3, on CPU so
it never disturbs GPU jobs); each joins the existing theme whose plots it is closest to, so theme names stay stable.
Prints 'changed' when themes.json was rewritten.
Files: theme_names.json, labels.json, centroids.npy, mean.npy (tracked) · embeddings.npy + embed_ids.json (local cache)."""
import json, base64, os, urllib.request, numpy as np
D = 256
def post(path, body):
    req = urllib.request.Request('http://localhost:11434' + path, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=900))
def embed(texts):
    out = []
    for i in range(0, len(texts), 16):
        out += post('/api/embed', {'model': 'bge-m3', 'input': texts[i:i+16], 'keep_alive': '1m', 'options': {'num_gpu': 0}})['embeddings']
    post('/api/generate', {'model': 'bge-m3', 'keep_alive': 0})
    return np.array(out, dtype=np.float32)

d = json.load(open('data.json'))
cur = {}
for t, key in (('movie', 'movies'), ('tv', 'tv_shows')):
    for it in d[key]:
        if (it.get('overview') or '').strip(): cur[f"{t}:{it['id']}"] = it['overview'].strip()[:2000]
names = json.load(open('theme_names.json'))
labels = json.load(open('labels.json'))
cent, mean = np.load('centroids.npy'), np.load('mean.npy')
if os.path.exists('embeddings.npy'):
    ids, X = json.load(open('embed_ids.json')), np.load('embeddings.npy')
else:
    ids, X = [], np.zeros((0, cent.shape[1]), np.float32)
have = set(ids)
new = [k for k in cur if k not in have]          # also re-reads everything if the cache was lost
if new:
    X = np.vstack([X, embed([cur[k] for k in new])]); ids += new
    np.save('embeddings.npy', X); json.dump(ids, open('embed_ids.json', 'w'))
Xn = X / np.linalg.norm(X, axis=1, keepdims=True)
Xc = Xn - mean
unl = [i for i, k in enumerate(ids) if k not in labels]
if unl:
    v = Xc[unl] / np.linalg.norm(Xc[unl], axis=1, keepdims=True)
    for i, th in zip(unl, np.argmax(v @ cent.T, 1)): labels[ids[i]] = int(th)
    json.dump(labels, open('labels.json', 'w'), separators=(',', ':'))
keep = [i for i, k in enumerate(ids) if k in cur]
out_ids = [ids[i] for i in keep]
old = json.load(open('themes.json')) if os.path.exists('themes.json') else {}
if not new and not unl and set(old.get('ids', [])) == set(out_ids) and old.get('themes') == names:
    print('no change'); raise SystemExit
P = Xc[keep]
_, _, Vt = np.linalg.svd(P, full_matrices=False)
P = P @ Vt[:D].T
P /= np.linalg.norm(P, axis=1, keepdims=True)
q = np.clip(np.round(P * 127 / np.abs(P).max()), -127, 127).astype(np.int8)
json.dump({'themes': names, 'ids': out_ids, 'theme': [labels[k] for k in out_ids], 'dim': D,
           'vec': base64.b64encode(q.tobytes()).decode()}, open('themes.json', 'w'), separators=(',', ':'))
print(f"changed: {len(new)} new, {len(out_ids)} titles")
for k in new[:40]: print('  +', k, '->', names[labels[k]])
