# Git Commit Script for DataPilot
# Run this script to stage and commit each modified file with a descriptive message.

Write-Host "Starting Git commits..." -ForegroundColor Cyan

# 1. README.md
git add README.md
git commit -m "docs: update project README documentation detailing application structure and workflow"

# 2. app.py
git add app.py
git commit -m "refactor(app): coordinate multi-page navigation and clean sidebar selector click behaviors"

# 3. assets/styles.css
git add assets/styles.css
git commit -m "style: define base CSS stylesheets, empty-state containers, and modern design cards"

# 4. pages/Analysis.py
git add pages/Analysis.py
git commit -m "feat(Analysis): add dynamic fallback to original dataset when no cleaning has occurred"

# 5. pages/BeforeAfter.py
git add pages/BeforeAfter.py
git commit -m "feat(BeforeAfter): implement Before vs After comparison engine with Plotly charts, column comparisons, and readiness checklist"

# 6. pages/Cleaning.py
git add pages/Cleaning.py
git commit -m "fix(Cleaning): resolve timeline log display bug showing raw HTML"

# 7. pages/Dashboard.py
git add pages/Dashboard.py
git commit -m "feat(Dashboard): implement main dashboard with overall quality score and health counters"

# 8. pages/Download.py
git add pages/Download.py
git commit -m "style(Download): replace raw warning alerts with standardized empty-state card layout"

# 9. pages/Reports.py
git add pages/Reports.py
git commit -m "style(Reports): replace raw warning alerts with standardized empty-state card layout"

# 10. pages/Settings.py
git add pages/Settings.py
git commit -m "feat(Settings): structure settings configurations page"

# 11. utils/cleaner.py
git add utils/cleaner.py
git commit -m "feat(utils): implement core outlier handling, datatype parsing, and text standardization helpers"

# 12. utils/helpers.py
git add utils/helpers.py
git commit -m "feat(utils): implement rule-based Data Quality score algorithms and categories health labels"

Write-Host "All commits completed successfully!" -ForegroundColor Green
