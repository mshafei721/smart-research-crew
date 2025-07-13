# Force Browser Refresh Instructions

## The web components error is NOT related to SSE - ignore it!

## To force browser refresh and test SSE:

### Method 1: Hard Refresh
1. Hold **Ctrl+Shift** and click the **Refresh button**
2. OR press **Ctrl+F5** (Windows) / **Cmd+Shift+R** (Mac)

### Method 2: Clear Cache
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

### Method 3: Incognito/Private Mode
1. Open incognito/private browser window
2. Go to http://localhost:5173
3. Test SSE functionality

### What to Look For:
After hard refresh, when you click "Launch Research", you should see in console:
```
Creating EventSource with URL: /sse?topic=...
Full URL will resolve to: http://localhost:5173/sse?...
SSE connection opened
```

### If Still Not Working:
Test the simple page: http://localhost:5173/test-sse.html