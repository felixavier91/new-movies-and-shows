# 🎬 Fresh Movies & TV Shows - Last 365 Days

A simple, auto-updating website showing the freshest movies and TV shows from the last year. Updates every hour via GitHub Actions.

## 🚀 Features

- ✅ Shows movies & TV shows from the **last 365 days only**
- ✅ Auto-updates **every hour** via GitHub Actions
- ✅ Clean, minimal UI with **shuffle** and **keyword search**
- ✅ Hosted for free on **GitHub Pages**
- ✅ Only 3 files - super simple!

## 📁 File Structure

```
your-repo/
├── .github/
│   └── workflows/
│       └── update-data.yml    # Hourly cron job
├── index.html                  # Website UI
├── fetch_data.py              # Data fetcher script
├── data.json                  # Auto-generated (updates hourly)
└── README.md                  # This file
```

## 🛠️ Setup Instructions

### 1. Create GitHub Repository

1. Create a new repository on GitHub
2. Clone it locally or use GitHub's web interface

### 2. Add Your Files

Copy these 3 files into your repo:
- `index.html`
- `fetch_data.py`
- `.github/workflows/update-data.yml`

### 3. Configure TMDB API Token

1. Get your TMDB API Read Access Token from https://www.themoviedb.org/settings/api
2. In your GitHub repo, go to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `TMDB_TOKEN`
5. Value: Paste your TMDB API token
6. Click **"Add secret"**

### 4. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under **Source**, select **"GitHub Actions"**
3. Save

### 5. Run First Data Fetch

1. Go to **Actions** tab
2. Click on **"Update TMDB Data Hourly"** workflow
3. Click **"Run workflow"** → **"Run workflow"** (green button)
4. Wait 10-20 minutes for it to complete
5. Your site will be live at: `https://yourusername.github.io/your-repo-name/`

## ⚙️ Configuration

Edit these values in `fetch_data.py` to customize what data is fetched:

```python
# ============= CONFIGURATION (EDIT THESE) =============
MIN_VOTES = 100          # Minimum number of reviews/votes
MIN_RATING = 6.0         # Minimum TMDB rating (0-10)
DAYS_BACK = 365          # How many days back to fetch (365 = last year)
MAX_PAGES_PER_TYPE = 50  # Max pages to fetch per content type
```

**Examples:**
- Want only highly-rated content? Change `MIN_RATING = 7.5`
- Want more obscure titles? Change `MIN_VOTES = 50`
- Want last 6 months only? Change `DAYS_BACK = 180`
- Want more results? Change `MAX_PAGES_PER_TYPE = 100`

After changing, commit and push - the next hourly run will use the new settings.

## 🕐 How It Works

1. **Every hour** (at :00 minutes), GitHub Actions runs `fetch_data.py`
2. Python script calls TMDB API for movies/TV from last 365 days
3. Optimized API calls using `append_to_response` (gets credits + providers in 1 call)
4. Generates `data.json` with all the data
5. Commits `data.json` to the repo (if changed)
6. GitHub Pages automatically updates your website

## 📊 What Gets Fetched

For each movie/TV show:
- Title, overview, poster
- Release date, year
- TMDB rating and vote count
- Director (movies only)
- Top 3 actors
- Streaming providers (US only)

## 🎨 UI Features

- **Shuffle**: Randomize the order of movies/shows
- **Restore**: Go back to original order (newest first)
- **Search**: Filter by title, actor, or director
- **Hover cards**: See details on hover
- **Responsive**: Works on mobile and desktop

## ⚡ Performance

- **API calls**: ~1-2 calls per title (optimized with `append_to_response`)
- **Rate limit**: 40 requests per 10 seconds (TMDB limit)
- **Fetch time**: ~10-20 minutes for typical dataset
- **File size**: ~10-30 MB JSON (depending on results)

## 🔧 Local Testing

Want to test before pushing to GitHub?

```bash
# 1. Install Python dependencies
pip install requests

# 2. Set your TMDB token
export TMDB_TOKEN="your_token_here"

# 3. Run the fetch script
python fetch_data.py

# 4. Serve the site locally
python -m http.server 8000

# 5. Open http://localhost:8000 in browser
```

## 📝 Notes

- First run takes 10-20 minutes (fetching all data)
- Subsequent runs are faster (only checks for new content)
- `data.json` only updates if there are actual changes
- TMDB has rate limits: 40 requests per 10 seconds
- Script automatically handles rate limiting
- Cron runs at :00 of every hour (not exactly 60 min apart)

## 🐛 Troubleshooting

**"Error loading data" on website:**
- Check if `data.json` exists in your repo
- Make sure GitHub Actions ran successfully (check Actions tab)
- Try running workflow manually

**Actions failing:**
- Check if `TMDB_TOKEN` secret is set correctly
- Look at the workflow logs for specific errors
- Make sure `fetch_data.py` has correct permissions

**No data showing:**
- Check if your MIN_VOTES and MIN_RATING are too strict
- Try lowering them in `fetch_data.py`
- Check console for JavaScript errors

## 📄 License

MIT - Do whatever you want with this!

---

**Made with ❤️ for fresh content discovery**
