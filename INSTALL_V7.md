# V7 Installation Instructions

## Quick Setup

1. **Download both files:**
   - `checker.py`
   - `HANDOFF_V7.md`

2. **Create directory and move files:**
   ```bash
   mkdir -p ~/Documents/Claude/shopify-theme-checker-7
   mv ~/Downloads/checker.py ~/Documents/Claude/shopify-theme-checker-7/
   mv ~/Downloads/HANDOFF_V7.md ~/Documents/Claude/shopify-theme-checker-7/
   ```

3. **Install dependencies (if not already installed):**
   ```bash
   pip3 install requests beautifulsoup4
   ```

4. **Update terminal alias:**
   ```bash
   # Open .zshrc
   nano ~/.zshrc
   
   # Find and update the check-stores alias to:
   alias check-stores='cd ~/Documents/Claude/shopify-theme-checker-7 && python3 checker.py'
   
   # Save and reload
   source ~/.zshrc
   ```

5. **Test it:**
   ```bash
   check-stores
   ```

## What Changed from V6

### New Features:
- **Brand Name:** Extracted from store metadata
- **Contact Email:** Found from footer/contact sections
- **Auto-width Table:** Adjusts to your terminal size
- **Full Issues Text:** No more "..." truncation

### Table Columns (left to right):
1. STORE - myshopify.com URL
2. BRAND - Store brand name
3. CONTACT - Public email or "No public email found"
4. RISK - 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW
5. STATUS - ✅ Active / 🚫 Uninstalled
6. ISSUES DETECTED - Full text, no truncation

## Usage Tips

- **Wider terminal = More space for issues:** Maximize your terminal window for best results
- **Brand name helps personalization:** Use in outreach emails
- **Contact email saves time:** Direct outreach without hunting for emails
- **"No public email found":** Check their Shopify Partners dashboard for registration email

## Troubleshooting

**Table still looks cut off?**
- Make your terminal window wider
- Minimum recommended width: 120 characters
- Optimal width: 160+ characters

**Missing brand names?**
- Some stores don't set proper metadata
- Will show "Unknown" in these cases

**No contact emails found?**
- Many stores don't publish emails on homepage/footer
- You'll need to check contact page manually or use Partners dashboard
