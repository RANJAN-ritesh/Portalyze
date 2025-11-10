# Playwright on Render - Setup Guide

## Issue

Modern portfolios (React, Vue, Next.js) render content via JavaScript. Without JavaScript execution, the analyzer only sees an empty HTML skeleton, resulting in low scores (15%) even for good portfolios.

**Example:**
- Portfolio: https://myportfolio-manjari5506.vercel.app/
- Without Playwright: `<div id="root"></div>` (empty!)
- With Playwright: Full rendered HTML with all sections

---

## Solution Applied

### Changes Made:

1. **requirements.txt** - Enabled Playwright:
   ```python
   playwright>=1.48.0  # Enabled for production
   ```

2. **render.yaml** - Added Playwright browser installation:
   ```yaml
   buildCommand: pip install --upgrade pip && pip install -r requirements.txt && playwright install --with-deps chromium
   ```

3. **Code** - Already has automatic fallback:
   ```python
   if PLAYWRIGHT_AVAILABLE:
       return await self._fetch_with_playwright(url)
   else:
       return await self._fetch_with_aiohttp(url)  # Fallback
   ```

---

## Expected Behavior After Deploy

### ✅ With Playwright Working:
```
✅ JavaScript-rendered portfolios: Accurate scores (80-90%)
✅ All sections detected (About, Projects, Skills, Contact)
✅ Full rubric validation (27 parameters)
✅ Responsive testing (mobile/tablet/desktop)
⚠️  Slower analysis (~3-5s per portfolio)
⚠️  Higher memory usage
```

### ⚠️ If Playwright Fails (Fallback to aiohttp):
```
✅ Static HTML portfolios: Accurate scores
❌ JS-rendered portfolios: Low scores (15-30%)
❌ Empty content detected
✅ Fast analysis (~0.5s per portfolio)
✅ Low memory usage
```

---

## Potential Issues on Render Free Tier

### 1. Build Timeout
**Symptom:** Build fails after 15+ minutes
**Cause:** Downloading Chromium takes too long
**Solution:** Upgrade to paid tier or use alternative

### 2. Memory Limits
**Symptom:** Service crashes during analysis
**Cause:** Chromium needs ~200-300MB RAM
**Solution:** Reduce `MAX_CONCURRENT_ANALYSES` to 2-3

### 3. Disk Space
**Symptom:** "No space left" error
**Cause:** Chromium is ~300MB
**Solution:** Use Docker with multi-stage build

---

## Monitoring Playwright Status

### Check if Playwright is Available:

1. **Backend Health Check:**
   ```bash
   curl https://portalyze.onrender.com/health
   ```
   Look for: `"playwright_available": true`

2. **Backend Logs:**
   ```
   ✅ If working: "Using Playwright for fetching"
   ⚠️  If failed: "Playwright not available - using aiohttp fallback"
   ```

3. **Test a JS Portfolio:**
   ```bash
   curl -X POST https://portalyze.onrender.com/grade \
     -H "Content-Type: application/json" \
     -d '{"portfolio_url": "https://myportfolio-manjari5506.vercel.app/"}'
   ```
   Check score: Should be 70%+ if Playwright works

---

## Alternative Solutions

### Option 1: Use Playwright via Docker (Recommended)

Create `backend/Dockerfile`:
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.48.0-focal

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then deploy as Docker container on Render.

### Option 2: Use External Browser Service

Replace Playwright with:
- **Browserless.io** (paid, reliable)
- **ScrapingBee** (has free tier)
- **RenderTron** (self-hosted)

### Option 3: Warn Users About JS Portfolios

Add detection for JS-only portfolios:
```python
if len(html_content) < 1000:
    return {
        "warning": "Portfolio appears to be JavaScript-only. Score may be inaccurate.",
        "suggestion": "Ensure your portfolio has server-side rendering (SSR)"
    }
```

---

## Build Progress Tracking

After pushing changes, monitor Render build:

```
==> Building...
==> Installing dependencies...
==> Installing Playwright browsers...
    ⏳ Downloading Chromium... (2-5 minutes)
    ✅ Chromium installed successfully
==> Build successful 🎉
```

If it fails:
```
❌ playwright install failed
⚠️  Falling back to aiohttp
```

---

## Performance Impact

| Metric | aiohttp | Playwright |
|--------|---------|------------|
| Analysis Time | 0.5s | 3-5s |
| Memory Usage | 50MB | 300MB |
| Accuracy (JS portfolios) | 15-30% | 80-95% |
| Accuracy (Static portfolios) | 90-95% | 90-95% |

---

## Rollback Plan

If Playwright causes issues:

1. **Disable Playwright:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Or just comment out in requirements.txt:**
   ```python
   # playwright>=1.48.0  # Disabled due to Render limitations
   ```

3. **Code automatically falls back to aiohttp**

---

## Decision Matrix

### Use Playwright if:
- ✅ Most portfolios are React/Vue/Next.js
- ✅ Accuracy is critical
- ✅ You have paid Render plan or Docker setup

### Use aiohttp if:
- ✅ Most portfolios are static HTML
- ✅ Speed is critical
- ✅ You're on Render free tier
- ✅ Low resource usage needed

---

## Next Steps

1. Push changes to GitHub
2. Monitor Render build logs (~10-15 minutes)
3. Check if Playwright installs successfully
4. Test with JS portfolio
5. If fails, review alternatives above

---

**Status:** Attempting Playwright installation on Render
**ETA:** 10-15 minutes (build + deploy)
**Fallback:** aiohttp (already working)
