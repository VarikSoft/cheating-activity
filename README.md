<p align="center">
<a href="# 🛡️ Safe Usage"><b>👉 Read first: Safe Usage</b></a></p> 
<p align="center"> 
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" /> 
  <img src="https://img.shields.io/badge/status-beta-yellow?style=flat-square" /> 
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" /> 
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python" /> 
  <img src="https://img.shields.io/badge/GitHub%20API-REST%20v3-lightgrey?style=flat-square&logo=github" /> 
</p>

# ⏱️ GitHub Line-by-Line Committer

A tiny CLI that appends each line of text to a file in your GitHub repository and creates one commit per line via the Contents API. Supports fixed or randomized delay (e.g., 60, 60-120, 1m-2m, 500ms-2s), stdin/pipe input, dry-run, branch selection, and committer signature.

Great for journaling, build logs, or “activity bumping”.

# 🚀 Getting Started
``` bash
# 1) Put the script anywhere you like (repo root is convenient)
#    e.g., commit_lines_with_delay_en.py

# 2) Provide a token (classic PAT or fine-grained):
#    macOS/Linux
export GITHUB_TOKEN=your_token_here
#    Windows CMD
setx GITHUB_TOKEN your_token_here
#    Windows PowerShell
$env:GITHUB_TOKEN="your_token_here"

# 3) Run (examples below)
python commit_lines_with_delay_en.py --help
```

# 🛠️ Features

- Line-by-line commits — appends one line at a time and commits after each line.
- Randomized delay — --delay "60-120" picks a uniform random pause (in seconds) between commits. Units: ms, s, m, h.
- Multiple input sources — --text, --text-file, or standard input (pipe).
- Branch & path control — choose branch (--branch) and file path (--path). Creates the file if needed.
- Dry-run mode — preview commit messages without pushing (--dry-run).
- QoL flags — --skip-empty, --start-index, and a custom --commit-prefix.
- Commit author override — --committer-name / --committer-email.

# 🧪 Examples

## Fixed delay (90s):

python commit_lines_with_delay_en.py \
  --repo yourname/yourrepo \
  --path logs/notes.txt \
  --branch main \
  --text-file ./notes.txt \
  --commit-prefix "chore: note" \
  --delay 90


## Random delay (60–120s):

python commit_lines_with_delay_en.py \
  --repo yourname/yourrepo \
  --path README.md \
  --branch main \
  --text "first line\nsecond line\nthird line" \
  --delay "60-120"


## With units (1–2 minutes):

python commit_lines_with_delay_en.py \
  --repo yourname/yourrepo \
  --path logs/log.txt \
  --branch main \
  --text-file ./big.txt \
  --skip-empty \
  --delay "1m-2m"


## Dry-run preview:

python commit_lines_with_delay_en.py \
  --repo yourname/yourrepo \
  --path logs/notes.txt \
  --text-file ./notes.txt \
  --dry-run


# Works on Windows (CMD/PowerShell), macOS, and Linux. Python 3.10+ required.

``` bash
⚙️ CLI Options
--repo              owner/repo (e.g., yourname/yourrepo)  [required]
--path              File path in the repo (e.g., logs/notes.txt)  [required]
--branch            Branch name (default: main)
--text              Inline text (split by lines)
--text-file         Read text from a local file
--delay             Fixed or range:
                    - "60" (seconds)
                    - "60-120" (uniform range in seconds)
                    - "500ms-2s", "1m-2m", "1h-2h" (units: ms,s,m,h)
--skip-empty        Skip empty lines
--start-index       Start from this 0-based line index (default: 0)
--commit-prefix     Commit message prefix (default: "chore: append line")
--committer-name    Committer display name (optional)
--committer-email   Committer email (optional)
--token             Personal Access Token (or use env GITHUB_TOKEN)
--dry-run           Show planned commits without pushing
```

> [!TIP]
> - If the repo is empty (no commits), create an initial commit first (e.g., a tiny README) before using the Contents API.
> - If the file already exists, the script appends; if not, it will create it.
> - Use --dry-run to validate target branch/path and messages before pushing.
> - For org repos, make sure your token is SSO-authorized.

# 🛡️ Safe Usage

Use the script responsibly to keep your account in good standing:

- Official limits to respect

  * Primary REST rate limit: authenticated users can make up to 5,000 requests per hour. A single commit via this script uses 1 API write (one PUT /contents), so this is a very high ceiling for typical usage. 

  * Content creation (secondary) limits: in general, no more than 80 content-generating requests per minute and no more than 500 per hour across web/API. Treat this as the practical hard cap on commits/hour for tools like this that create content via the API. Some endpoints may have lower limits, and these secondary limits can change. 

- Commit meaningful content
Use this for real notes, logs, or progressive output—not empty or low-value lines purely to “green up” contribution graphs.

- Keep a moderate pace
Randomize pauses with --delay "60-120" or similar. Avoid bursts of many rapid commits or running multiple parallel instances.

- Protect your token
Store it in GITHUB_TOKEN, grant minimum scopes (public_repo for public repos, repo for private), and revoke/rotate immediately if it leaks. For org repos, ensure the token is SSO-authorized.

- Be transparent in teams
In shared repos, clarify intent with a clear --commit-prefix (e.g., chore: daily notes).

- When in doubt, slow down
If activity looks noisy, either increase delays or batch related lines into fewer commits.

Contributions and issues are welcome!
