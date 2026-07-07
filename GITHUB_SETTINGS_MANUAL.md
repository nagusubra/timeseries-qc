# GitHub Repository Settings - Manual Configuration Required

These settings must be configured manually via the GitHub web interface as they require repository admin permissions.

## 1. Repository Topics/Tags

**Location:** Repository homepage → Settings → About → Topics

**Add these 20 topics:**
```
timeseries
data-quality
scada
data-validation
historian
iot
industrial-iot
time-series-analysis
pandas
plotly
python-library
data-engineering
sensor-data
dcs
opc-ua
osisoft-pi
outlier-detection
data-cleansing
energy-sector
manufacturing
```

**Why:** Topics improve GitHub search and discoverability. Developers and AI agents search for these specific terms.

---

## 2. Repository Description

**Location:** Repository homepage → Settings → About → Description

**New description:**
```
Time series data quality control for SCADA, DCS & historian data. Tag every row as good/suspect/bad with 5 built-in rules (null, flatline, delta, range, outlier), YAML config, and Plotly timeline charts. MIT licensed.
```

**Current:** "An open source library to execute quality checks on timeseries data."

**Why:** Includes primary search keywords and value proposition.

---

## 3. Homepage URL

**Location:** Repository homepage → Settings → About → Website

**Set to:**
```
https://nagusubra.github.io/timeseries-qc/
```

**Why:** Drives traffic to comprehensive documentation; shows professionalism.

---

## 4. Social Preview Image

**Location:** Repository homepage → Settings → Social preview → Upload

**File:** `docs/assets/images/social-preview.png` (needs to be created - see instructions below)

**Specs:**
- Dimensions: 1200x630 pixels
- Format: PNG or JPG
- Max file size: 1MB

**Content to include:**
- Library name: timeseries-qc
- Tagline: "Data Quality Control for SCADA & Historian Data"
- Screenshot of timeline chart
- Key features bullets
- GitHub stars badge
- Install command: `pip install timeseries-qc`

**Colors to use:**
- Primary: #2563eb (blue)
- Good: #10b981 (green)
- Suspect: #f59e0b (yellow)
- Bad: #ef4444 (red)

**Why:** Social preview images increase click-through rates by 5x on Twitter, LinkedIn, Slack, Discord.

---

## 5. Enable GitHub Discussions

**Location:** Repository → Settings → Features → Discussions → Enable

**Categories to create:**

1. **📢 Announcements** (Maintainers only)
   - Description: Release notes and important updates

2. **💡 Ideas**
   - Description: Feature requests and brainstorming

3. **❓ Q&A** (Enable "Mark as answer")
   - Description: Ask technical questions

4. **🎉 Show and Tell**
   - Description: Share your projects and success stories

5. **🔧 Troubleshooting**
   - Description: Get help with problems

6. **🏭 SCADA & Historian**
   - Description: Industry-specific discussions (OSIsoft PI, OPC UA, etc.)

7. **💬 General**
   - Description: Everything else

**Initial discussions to create:**
- "Welcome to timeseries-qc! Introduce yourself" (in General)
- "Share your use case and data source" (in Show and Tell)
- "Feature roadmap discussion" (in Ideas)

**Why:** 
- Builds community
- AI agents can reference discussions
- Reduces duplicate issues
- Better SEO (Google indexes discussions)

---

## 6. Repository Settings Checklist

**General Settings:**
- ✅ Features → Issues: Enabled
- ✅ Features → Discussions: Enabled (see above)
- ✅ Features → Projects: Enabled
- ✅ Pull Requests → Allow squash merging: Enabled
- ✅ Pull Requests → Allow merge commits: Enabled
- ✅ Pull Requests → Automatically delete head branches: Enabled

**Security:**
- ✅ Code scanning → CodeQL: Already enabled
- ✅ Secret scanning: Enabled
- ✅ Dependabot alerts: Enabled

**Pages:**
- ✅ Source: gh-pages branch (already configured)
- ✅ Custom domain: None
- ✅ Enforce HTTPS: Enabled

---

## Verification

After making these changes:

1. **Check topics:** Visit repository page, should see all 20 topics listed
2. **Check description:** Should appear under repository name
3. **Check homepage:** Click the link icon next to description
4. **Check social preview:** Share the repository link on Slack/Discord to test
5. **Check discussions:** Navigate to repository → Discussions tab

---

## Status

- [x] Issue templates created (.github/ISSUE_TEMPLATE/)
- [ ] Topics added (manual - see instructions above)
- [ ] Description updated (manual - see instructions above)
- [ ] Homepage URL set (manual - see instructions above)
- [ ] Social preview image uploaded (manual - needs image creation)
- [ ] GitHub Discussions enabled (manual - see instructions above)
