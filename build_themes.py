"""Build themes.json from embeddings.npy + labels.npy (run embed.py, then cluster.py 60, then this).
themes.json = theme names, each title's theme, and a small 'plot fingerprint' per title for the For-me ranking."""
import json, base64, numpy as np
NAMES = """College parties & teen comedies
City cops on a case
Stand-up comedy specials
American towns, ranches & frontier families
Marriages under strain
Fathers, daughters & desperate parents
Boxing & fighters
Lone man confronts his past
Spies, CIA & global conspiracies
Italian stories
Small-town & village new starts
Team sports & underdog coaches
Sweeping stories of love & life
Money, drugs & one job gone wrong
Heists & thieves
Period pieces: 1950s to 1980s
Hitmen & assassins on the run
An ordinary man's life takes a strange turn
Weddings & family expectations
Based on a true story
Small-town disappearances & murder
Summer, road trips & coming of age
Romance: meeting someone new
Zombies & outbreaks
Chinese epics & martial arts
Robots & AI
Old Britain & colonial-era drama
Revenge
Spanish-language crime & drama
Superheroes
Mothers, kids & family at home
French stories
Spain & Latin family dramas
High school: students & teachers
Boys, teens & strange discoveries
FBI & serial-killer procedurals
Prison & captivity
True-story & anthology series
Teen & young-adult series
Stranded: island, sea & wilderness survival
Couples & grown-up romance
Undercover cops & the underworld
Civil wars & ordinary people in wartime
Dogs, animals & family adventure
Girls growing up
Detective murder mysteries
First love & school friendships
Women with a past
Korean thrillers & dramas
Kings, queens & royal courts
Years later: sequels, returns & time jumps
Soldiers & military missions
Accidents, illness & second chances
Epic fantasy & saving the world
Siblings & estranged families
World War II & Nazi Germany
Space, aliens & Earth's future
Getaways gone wrong
Secrets in 20th-century America
Haunted houses & women in peril""".split('\n')
ids = json.load(open('embed_ids.json'))
lab = np.load('labels.npy')
assert len(NAMES) == lab.max() + 1
X = np.load('embeddings.npy'); X /= np.linalg.norm(X, axis=1, keepdims=True)
Xc = X - X.mean(0)
U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
D = 256
P = Xc @ Vt[:D].T
P /= np.linalg.norm(P, axis=1, keepdims=True)
# how well the short fingerprint keeps the full neighbours
full = Xc / np.linalg.norm(Xc, axis=1, keepdims=True)
rng = np.random.default_rng(0); s = rng.choice(len(ids), 200, replace=False)
a = np.argsort(-(full[s] @ full.T), 1)[:, 1:11]; b = np.argsort(-(P[s] @ P.T), 1)[:, 1:11]
print('top-10 neighbour overlap', np.mean([len(set(x) & set(y)) for x, y in zip(a, b)]) / 10)
q = np.clip(np.round(P * 127 / np.abs(P).max()), -127, 127).astype(np.int8)
json.dump({'themes': NAMES, 'ids': ids, 'theme': lab.tolist(), 'dim': D,
           'vec': base64.b64encode(q.tobytes()).decode()}, open('themes.json', 'w'), separators=(',', ':'))
print('themes.json written', len(ids))
