# Shopify Theme Compatibility Checker - V7 Handoff

**Current Status:** Working, V7 completed March 16, 2026  
**File Location:** `~/Documents/Claude/shopify-theme-checker-7/checker.py`  
**Terminal Alias:** `check-stores` (runs from anywhere)

## What V7 Does

Automatically scans Shopify stores from Slack notifications to detect Early Bird pre-order app compatibility issues.

### Key Features:

1. **Auto-width Table** - Detects terminal width and adjusts columns dynamically
2. **Brand Name** - Extracts from store metadata (title tag, og:site_name)
3. **Contact Email** - Extracts from footer/contact page
4. **Full Issues Text** - No truncation, shows complete list
5. **Deduplicates URLs** - Same store only checked once
6. **Tracks Uninstalls** - Parses "Uninstall from [store]" notifications
7. **Detects:**
   * Quick View/Add/Buy buttons
   * "Choose Options" buttons
   * Bundle products (build-a-bundle vs pre-made)
   * Product recommendations with Quick Add
   * Subscription apps (Recharge, Appstle, etc.)
   * Try-before-you-buy features
   * Theme name
   * Risk level (HIGH/MEDIUM/LOW)

## How to Use

```bash
check-stores
# Paste Slack notifications from #early-bird and #early-bird-activity
# Press ENTER twice
```

**Slack Format Supported:**
```
New install from Store Name (store.myshopify.com)!
Uninstall from Store Name (store.myshopify.com).
Published "Campaign" from Store (store.myshopify.com).
```

## Example Output

```
✅ Found 59 activities from 15 unique store(s)
⚠️  3 store(s) uninstalled (marked in summary)
🔍 Checking 15 store(s)...

📊 SUMMARY - ALL STORES
STORE                    BRAND                  CONTACT                      RISK      STATUS         ISSUES DETECTED
------------------------------------------------------------------------------------------------------------------------
store1.myshopify.com    AMTTPE Official        support@amttpe.com           🔴 HIGH    ✅ Active      Quick add detected, Bundle products detected, Subscription app detected
store2.myshopify.com    Fashion Co             No public email found        🟡 MEDIUM  🚫 Uninstalled Subscription app detected
store3.myshopify.com    Tech Gadgets           contact@techgadgets.com      🟢 LOW     ✅ Active      No issues

Total Stores Checked: 15
  🔴 HIGH RISK: 3
  🟡 MEDIUM RISK: 10
  🟢 LOW RISK: 2
  🚫 UNINSTALLED: 3 (skip outreach)
```

## Version History

- **V7 (Current):** Brand name + contact email + auto-width table
- **V6:** Deduplication + uninstall tracking + summary table
- **V5:** Added summary table sorted by risk
- **V4:** Added recommendations, subscriptions, try-before-you-buy detection
- **V3:** Context-aware detection, batch processing
- **V2:** Element-based detection
- **V1:** Naive keyword matching

## What's New in V7

### 1. Brand Name Extraction
- Pulls from `og:site_name` meta tag (most reliable)
- Falls back to `<title>` tag
- Shows "Unknown" if not found

### 2. Contact Email Extraction
- Searches footer for `mailto:` links
- Looks for email patterns in footer text
- Checks contact sections
- Shows "No public email found" if not available

### 3. Auto-width Table
- Detects terminal width automatically
- Adjusts column widths intelligently
- Prioritizes issues column (no truncation)
- Works on wide and narrow terminals

### 4. Column Priority
- **Fixed:** RISK (12 chars), STATUS (15 chars)
- **Flexible:** STORE, BRAND, CONTACT
- **Maximum:** ISSUES (gets remaining space, shows full text)

## Business Impact

* **Time saved:** 20+ hours/month (was 10-15 min per store manually)
* **Proactive support:** Contact HIGH RISK merchants with their brand name and email
* **Skip uninstalled stores:** Don't waste time on churned merchants
* **Better outreach:** Use brand name and contact email for personalized emails

## Dependencies

```bash
pip3 install requests beautifulsoup4
```

## Terminal Alias Setup

To use from anywhere:

```bash
# Add alias to .zshrc
echo 'alias check-stores="cd ~/Documents/Claude/shopify-theme-checker-7 && python3 checker.py"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

Or update existing alias:

```bash
alias check-stores='cd ~/Documents/Claude/shopify-theme-checker-7 && python3 checker.py'
```

## Future Improvements (Ideas)

- Export to CSV for easy import to CRM
- Webhook integration to auto-check new installs
- Email template generation based on risk factors
- Integration with Shopify Partners API for merchant contact info
