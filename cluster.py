"""One-off exploration tool used for the first grouping (prints keywords per cluster). The live process is refresh_themes.py."""
import json, sys, numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
K = int(sys.argv[1]) if len(sys.argv) > 1 else 60
d = json.load(open('data.json'))
by = {f"movie:{m['id']}": m for m in d['movies']} | {f"tv:{t['id']}": t for t in d['tv_shows']}
ids = json.load(open('embed_ids.json'))
X = np.load('embeddings.npy'); X /= np.linalg.norm(X, axis=1, keepdims=True)
Xc = X - X.mean(0); Xc /= np.linalg.norm(Xc, axis=1, keepdims=True)
km = KMeans(K, n_init=5, random_state=0).fit(Xc)
lab = km.labels_
np.save('labels.npy', lab)
cv = CountVectorizer(stop_words='english', min_df=5, ngram_range=(1, 2), max_features=30000)
C = cv.fit_transform([by[i]['overview'] for i in ids]); vocab = np.array(cv.get_feature_names_out())
tot = np.asarray(C.sum(0)).ravel() + 1
for k in range(K):
    idx = np.where(lab == k)[0]
    tf = np.asarray(C[idx].sum(0)).ravel()
    score = (tf / tf.sum()) * np.log(1 + C.shape[0] / tot) * np.log(1 + tf)
    words = ', '.join(vocab[np.argsort(-score)[:10]])
    cen = Xc[idx] @ km.cluster_centers_[k]
    top = [by[ids[j]]['title'] for j in idx[np.argsort(-cen)[:9]]]
    print(f"{k} n={len(idx)} | {words} | {'; '.join(top)}")
