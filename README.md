# Shopify Theme Compatibility Auditor

A command-line tool that scans a Shopify store's public storefront and flags features that commonly conflict with pre-order apps — quick add/buy buttons, bundles, subscription apps, and product recommendation widgets.

Built for [Early Bird](https://apps.shopify.com/early-bird-pre-order-manager), a Shopify pre-order app, to speed up manual compatibility checks on merchant stores before or after they install the app.

## What it does

Paste in one or more Shopify store URLs (or raw Slack-style install/uninstall notifications) and the tool will:

- Fetch each store's public homepage
- Detect the theme in use (where identifiable)
- Check for features that can bypass or conflict with a pre-order flow:
  - Quick View / Quick Add / Quick Buy buttons
  - "Choose options" buttons
  - Bundle products (pre-made or "build-a-bundle")
  - Product recommendation / cross-sell / upsell sections
  - Subscription apps (Recharge, Appstle, Seal Subscriptions, Smartrr, etc.)
- Pull the store's brand name and any publicly listed contact email from its homepage/footer
- Score each store LOW / MEDIUM / HIGH risk based on how many conflicting features are detected
- Print a summary table across all stores checked, sorted by risk level

Everything it reads is publicly available on the storefront — it does not access any private Shopify admin data, APIs, or credentials.

## Installation

```bash
git clone https://github.com/josiahwyk/shopify-theme-compatibility-auditor.git
cd shopify-theme-compatibility-auditor
pip3 install requests beautifulsoup4
```

## Usage

```bash
python3 checker.py
```

Paste one or more store URLs, one per line (either plain URLs or Slack-style notification text like `New install from Store Name (store.myshopify.com)!`), then press Enter twice to run the check. Type `quit` to exit.

Example input:

```
store1.myshopify.com
store2.myshopify.com

```

The tool will print a per-store report followed by a summary table, e.g.:

```
STORE                    BRAND              CONTACT                  RISK      STATUS     ISSUES DETECTED
store1.myshopify.com     Example Co         support@example.com      🔴 HIGH    ✅ Active   Quick add detected, Bundle products detected
store2.myshopify.com     Another Store      No public email found    🟢 LOW     ✅ Active   No issues
```

## Notes

- Detection is heuristic (pattern/keyword-based against page HTML), not exhaustive — treat risk levels as a starting point for manual review, not a guarantee.
- Only checks the homepage; some features (e.g. bundles on collection pages) may not surface if they aren't referenced there.
- No data is stored or sent anywhere outside your own machine — everything runs locally and output only goes to your terminal.

## License

All rights reserved. See [LICENSE](LICENSE). No permission is granted to use, copy, modify or distribute this code without prior written permission.
