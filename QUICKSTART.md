# 🚀 QUICK START GUIDE

## Setup Your GitHub Pages Site in 5 Minutes

### What You Need:
1. GitHub account
2. TMDB API token (free from https://www.themoviedb.org/settings/api)

### Files You Need:
1. **index-simple.html** → Rename to `index.html`
2. **fetch_data.py** → Keep as is
3. **.github/workflows/update-data.yml** → Keep folder structure

---

## Step-by-Step Setup:

### 1️⃣ Create GitHub Repository
```bash
# On GitHub.com:
# - Click "New repository"
# - Name it: fresh-movies (or whatever you want)
# - Make it Public
# - Don't initialize with README
# - Create repository
```

### 2️⃣ Upload Files

**Option A: Web Upload**
1. Click "uploading an existing file"
2. Drag and drop:
   - `index.html` (renamed from index-simple.html)
   - `fetch_data.py`
3. Create folder `.github/workflows/` and upload `update-data.yml`
4. Commit

**Option B: Git Command Line**
```bash
git clone https://github.com/yourusername/fresh-movies.git
cd fresh-movies

# Copy your files here
cp /path/to/index-simple.html index.html
cp /path/to/fetch_data.py .
mkdir -p .github/workflows
cp /path/to/update-data.yml .github/workflows/

git add .
git commit -m "Initial commit"
git push
```

### 3️⃣ Add TMDB Token Secret
1. In your repo, go to: **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Name: `TMDB_TOKEN`
4. Value: `your-tmdb-token-here`
5. Click **"Add secret"**

### 4️⃣ Enable GitHub Pages
1. Go to: **Settings** → **Pages**
2. Under **Source**: Select **"GitHub Actions"**
3. Click **Save**

### 5️⃣ Run First Data Fetch
1. Go to **Actions** tab
2. Click **"Update TMDB Data Hourly"**
3. Click **"Run workflow"** dropdown → **"Run workflow"** button
4. Wait 10-20 minutes (watch progress in Actions tab)
5. Once complete, your site is live at: `https://yourusername.github.io/fresh-movies/`

---

## 🎛️ Customize Settings

Edit `fetch_data.py` to change what gets fetched:

```python
MIN_VOTES = 100      # Lower = more obscure titles (try 50)
MIN_RATING = 6.0     # Higher = better quality (try 7.0)
DAYS_BACK = 365      # Last X days (try 180 for 6 months)
MAX_PAGES_PER_TYPE = 50  # More = longer fetch (try 100)
```

After editing, commit and push - next hourly run uses new settings!

---

## ⏰ Schedule (Automatic)

- Updates **every hour** at :00 minutes
- You can also manually trigger via Actions tab
- Only updates if new content is found

---

## 🎨 Your Site Features

✅ Shows movies & TV from last 365 days (fresh content only!)  
✅ **Shuffle** - randomize order  
✅ **Restore** - back to newest first  
✅ **Search** - filter by title, actor, director  
✅ Clean, fast, mobile-friendly  

---

## 📊 What You'll Get

Typical dataset (with default settings):
- ~500-1500 movies
- ~300-800 TV shows
- Total: ~800-2300 items
- JSON size: ~15-30 MB
- Updates hourly automatically!

---

## ❓ Troubleshooting

**Site not loading?**
- Check if `data.json` exists in repo
- Make sure Actions workflow completed successfully

**No data showing?**
- Settings might be too strict
- Try: `MIN_VOTES = 50` and `MIN_RATING = 5.5`

**Actions failing?**
- Check if TMDB_TOKEN secret is set
- Look at workflow logs for errors

---

## 🎉 You're Done!

Your site auto-updates every hour with fresh content from the last 365 days!

**Share your site:** `https://yourusername.github.io/fresh-movies/`

---

**Need help?** Check README-setup.md for detailed documentation.
