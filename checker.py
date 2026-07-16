#!/usr/bin/env python3
"""
Shopify Theme Compatibility Checker - V7
Scans a merchant's store to detect potential pre-order compatibility issues

V7 Updates (March 2026):
- Auto-detects terminal width for optimal table display
- Extracts brand name from store metadata
- Extracts contact email from footer/contact page
- Shows full issues text without truncation

V6 Updates (March 2026):
- Deduplicates store URLs (same store only checked once)
- Tracks uninstalls from Slack notifications
- Shows uninstall status in summary table
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import shutil

def fetch_store_page(url):
    """
    Fetch the HTML content of a store page.
    
    Args:
        url: The store URL to check
        
    Returns:
        HTML content as string, or None if fetch fails
    """
    # Ensure URL has proper format
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"⚠️  Failed to fetch page. Status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return None


def extract_brand_name(html):
    """
    Extract brand/store name from page metadata.
    
    Args:
        html: HTML content
        
    Returns:
        Brand name string or "Unknown"
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try og:site_name first (most reliable for Shopify stores)
    og_site_name = soup.find('meta', property='og:site_name')
    if og_site_name and og_site_name.get('content'):
        return og_site_name['content'].strip()
    
    # Try title tag (remove " – Shopify store name" suffix if present)
    title = soup.find('title')
    if title and title.string:
        brand = title.string.strip()
        # Clean up common Shopify patterns
        brand = re.sub(r'\s*[–-]\s*.*$', '', brand)  # Remove everything after dash
        return brand
    
    # Fallback: try og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()
    
    return "Unknown"


def extract_contact_email(html):
    """
    Extract contact email from footer or contact sections.
    
    Args:
        html: HTML content
        
    Returns:
        Email address string or "No public email found"
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look in footer first (most common location)
    footer = soup.find('footer')
    if footer:
        # Find mailto links
        mailto = footer.find('a', href=re.compile(r'^mailto:', re.IGNORECASE))
        if mailto:
            email = mailto['href'].replace('mailto:', '').strip()
            # Clean up query parameters if any
            email = email.split('?')[0]
            return email
        
        # Look for email patterns in footer text
        footer_text = footer.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, footer_text)
        if emails:
            return emails[0]  # Return first found email
    
    # Look for contact sections
    contact_sections = soup.find_all(['div', 'section'], class_=re.compile(r'contact', re.IGNORECASE))
    for section in contact_sections:
        mailto = section.find('a', href=re.compile(r'^mailto:', re.IGNORECASE))
        if mailto:
            email = mailto['href'].replace('mailto:', '').strip()
            email = email.split('?')[0]
            return email
        
        # Look for email patterns in contact section text
        section_text = section.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, section_text)
        if emails:
            return emails[0]
    
    # Last resort: search entire page for mailto links
    all_mailto = soup.find_all('a', href=re.compile(r'^mailto:', re.IGNORECASE))
    if all_mailto:
        email = all_mailto[0]['href'].replace('mailto:', '').strip()
        email = email.split('?')[0]
        return email
    
    return "No public email found"


def check_quick_buttons(html):
    """
    Check for quick view, quick add, quick buy buttons.
    More accurate detection by looking for actual button elements and visible text.
    
    Returns:
        dict with detected features
    """
    soup = BeautifulSoup(html, 'html.parser')
    html_lower = html.lower()
    
    findings = {
        'quick_view': False,
        'quick_add': False,
        'quick_buy': False,
        'choose_options': False
    }
    
    # Check for Quick View - look for buttons/links with these patterns
    quick_view_buttons = soup.find_all(['button', 'a'], class_=re.compile(r'quick.?view', re.IGNORECASE))
    quick_view_text = soup.find_all(['button', 'a'], string=re.compile(r'quick.?view', re.IGNORECASE))
    if quick_view_buttons or quick_view_text:
        findings['quick_view'] = True
    
    # Check for Quick Add - common in Dawn theme and variants
    # Also includes "Add to Cart" on collection pages (same functionality, different label)
    quick_add_buttons = soup.find_all(['button', 'a'], class_=re.compile(r'quick.?add|quick-shop|product.?card.*add', re.IGNORECASE))
    quick_add_text = soup.find_all(['button', 'a'], string=re.compile(r'quick.?add|add to cart', re.IGNORECASE))
    # Also check for data attributes commonly used
    quick_add_data = soup.find_all(attrs={'data-quick-add': True}) or soup.find_all(attrs={'data-quickadd': True})
    
    # Check if "Add to Cart" buttons appear on product cards (collection page pattern)
    product_cards = soup.find_all(['div', 'article'], class_=re.compile(r'product.?card|product.?item|collection.?item', re.IGNORECASE))
    for card in product_cards[:5]:  # Check first 5 product cards
        add_to_cart_btn = card.find_all(['button', 'a'], string=re.compile(r'add to cart', re.IGNORECASE))
        if add_to_cart_btn:
            findings['quick_add'] = True
            break
    
    if quick_add_buttons or quick_add_text or quick_add_data:
        findings['quick_add'] = True
    
    # Check for Quick Buy
    quick_buy_buttons = soup.find_all(['button', 'a'], class_=re.compile(r'quick.?buy', re.IGNORECASE))
    quick_buy_text = soup.find_all(['button', 'a'], string=re.compile(r'quick.?buy', re.IGNORECASE))
    if quick_buy_buttons or quick_buy_text:
        findings['quick_buy'] = True
    
    # Check for "Choose options" button - very common with variants
    choose_options_buttons = soup.find_all(['button', 'a'], string=re.compile(r'choose\s+options?', re.IGNORECASE))
    choose_options_class = soup.find_all(['button', 'a'], class_=re.compile(r'choose.?options?', re.IGNORECASE))
    if choose_options_buttons or choose_options_class:
        findings['choose_options'] = True
    
    return findings


def check_bundles(html):
    """
    Check for bundle products, bundle apps, and build-a-bundle features.
    
    Returns:
        dict with bundle detection info
    """
    soup = BeautifulSoup(html, 'html.parser')
    html_lower = html.lower()
    
    findings = {
        'bundles_detected': False,
        'bundle_type': None,
        'bundle_indicators': []
    }
    
    # Build-a-bundle patterns (like Putt Buddies)
    build_bundle_patterns = [
        'build a bundle',
        'build your bundle',
        'create a bundle',
        'create your bundle',
        'custom bundle',
        'bundle builder',
        'make your own bundle',
        '/apps/gbb/',  # Common bundle app URL pattern
        'easybundle'
    ]
    
    # Pre-made bundle patterns
    premade_bundle_patterns = [
        'product-bundle',
        'bundle-product',
        'bundlebuilder',
        'frequently bought together',
        'buy together',
        'bundle deal',
        'bundle & save',
        'save with bundles'
    ]
    
    # Check for build-a-bundle first (higher priority)
    for pattern in build_bundle_patterns:
        if pattern in html_lower:
            findings['bundles_detected'] = True
            findings['bundle_type'] = 'Build-a-Bundle'
            findings['bundle_indicators'].append(pattern)
    
    # If no build-a-bundle found, check for pre-made bundles
    if not findings['bundles_detected']:
        for pattern in premade_bundle_patterns:
            if pattern in html_lower:
                findings['bundles_detected'] = True
                findings['bundle_type'] = 'Pre-made Bundles'
                findings['bundle_indicators'].append(pattern)
    
    return findings


def check_featured_sections(html):
    """
    Check for featured product sections on homepage.
    
    Returns:
        dict with section detection info
    """
    soup = BeautifulSoup(html, 'html.parser')
    html_lower = html.lower()
    
    findings = {
        'featured_products': False,
        'featured_collection': False,
        'section_count': 0
    }
    
    # Look for featured product sections
    featured_patterns = ['featured-product', 'featured_product', 'featured collection']
    for pattern in featured_patterns:
        if pattern in html_lower:
            findings['featured_products'] = True
            break
    
    # Count product sections (rough estimate)
    product_sections = soup.find_all(['section', 'div'], class_=re.compile(r'product|collection|featured'))
    findings['section_count'] = len(product_sections)
    
    return findings


def check_recommendations(html):
    """
    Check for cross-sell, upsell, and product recommendation sections.
    These often have Quick Add buttons that bypass Early Bird.
    
    Returns:
        dict with recommendation section detection
    """
    soup = BeautifulSoup(html, 'html.parser')
    html_lower = html.lower()
    
    findings = {
        'recommendations_detected': False,
        'recommendation_types': [],
        'has_quick_add': False
    }
    
    # Recommendation patterns
    rec_patterns = [
        ('you may also like', 'You May Also Like'),
        ('recommended for you', 'Recommended For You'),
        ('complete the look', 'Complete The Look'),
        ('shop the look', 'Shop The Look'),
        ('frequently bought together', 'Frequently Bought Together'),
        ('customers also bought', 'Customers Also Bought'),
        ('related products', 'Related Products'),
        ('similar products', 'Similar Products'),
        ('product-recommendations', 'Product Recommendations'),
        ('cross-sell', 'Cross-sell'),
        ('upsell', 'Upsell')
    ]
    
    for pattern, display_name in rec_patterns:
        if pattern in html_lower:
            findings['recommendations_detected'] = True
            if display_name not in findings['recommendation_types']:
                findings['recommendation_types'].append(display_name)
    
    # Check if recommendation sections have Quick Add buttons
    rec_sections = soup.find_all(['section', 'div'], class_=re.compile(r'recommend|related|cross-sell|upsell|also-bought', re.IGNORECASE))
    for section in rec_sections:
        quick_add = section.find_all(['button', 'a'], class_=re.compile(r'quick.?add', re.IGNORECASE))
        if quick_add:
            findings['has_quick_add'] = True
            break
    
    return findings


def check_subscriptions(html):
    """
    Check for subscription apps and features.
    These are incompatible with Early Bird pre-orders.
    
    Returns:
        dict with subscription detection
    """
    soup = BeautifulSoup(html, 'html.parser')
    html_lower = html.lower()
    
    findings = {
        'subscription_detected': False,
        'subscription_apps': [],
        'has_subscribe_save': False
    }
    
    # Subscription app patterns
    sub_apps = [
        ('recharge', 'Recharge'),
        ('appstle', 'Appstle'),
        ('seal subscriptions', 'Seal Subscriptions'),
        ('smartrr', 'Smartrr'),
        ('subscription', 'Generic Subscription'),
        ('subscribe', 'Subscribe & Save'),
        ('recurring', 'Recurring Orders')
    ]
    
    for pattern, app_name in sub_apps:
        if pattern in html_lower:
            findings['subscription_detected'] = True
            if app_name not in findings['subscription_apps']:
                findings['subscription_apps'].append(app_name)
    
    # Check for subscribe & save buttons
    sub_buttons = soup.find_all(['button', 'label', 'div'], string=re.compile(r'subscribe\s*(&|and)?\s*save', re.IGNORECASE))
    sub_classes = soup.find_all(class_=re.compile(r'subscribe.*save|subscription', re.IGNORECASE))
    if sub_buttons or sub_classes:
        findings['has_subscribe_save'] = True
    
    return findings


def detect_theme(html):
    """
    Detect the Shopify theme being used.
    
    Returns:
        Theme name as string
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check meta generator tag
    generator = soup.find('meta', attrs={'name': 'generator'})
    if generator and 'content' in generator.attrs:
        content = generator['content']
        # Extract theme name if present
        if 'Shopify' in content:
            return 'Shopify (Theme unknown)'
    
    # Check for common theme identifiers in classes or data attributes
    theme_indicators = {
        'dawn': 'Dawn',
        'debut': 'Debut',
        'narrative': 'Narrative',
        'brooklyn': 'Brooklyn',
        'minimal': 'Minimal',
        'supply': 'Supply',
        'venture': 'Venture',
        'boundless': 'Boundless',
        'simple': 'Simple',
        'empire': 'Empire'
    }
    
    html_lower = html.lower()
    for indicator, theme_name in theme_indicators.items():
        if f'theme-{indicator}' in html_lower or f'theme_{indicator}' in html_lower:
            return theme_name
    
    return "Unknown Theme"


def calculate_risk_level(quick_buttons, bundles, featured, recommendations, subscriptions):
    """
    Calculate overall risk level based on detected features.
    
    Returns:
        tuple: (risk_level, risk_factors)
    """
    risk_factors = []
    
    # Quick buttons detection
    if quick_buttons['quick_add']:
        risk_factors.append("Quick add detected")
    if quick_buttons['quick_view']:
        risk_factors.append("Quick view/buy buttons")
    if quick_buttons['choose_options']:
        risk_factors.append("Choose options button")
    
    # Bundle detection
    if bundles['bundles_detected']:
        risk_factors.append("Bundle products detected")
    
    # Recommendations
    if recommendations['recommendations_detected']:
        risk_factors.append("Product recommendations with quick add")
    
    # Subscriptions
    if subscriptions['subscription_detected']:
        risk_factors.append("Subscription app detected")
    
    # Calculate risk level
    if len(risk_factors) >= 3:
        return 'HIGH', risk_factors
    elif len(risk_factors) >= 1:
        return 'MEDIUM', risk_factors
    else:
        return 'LOW', risk_factors


def generate_report(store_url, theme, quick_buttons, bundles, featured, recommendations, subscriptions, risk_level, risk_factors):
    """
    Generate detailed report for a single store.
    """
    print(f"\n🏪 Store: {store_url}")
    print(f"🎨 Theme: {theme}")
    
    # Risk level with color coding
    if risk_level == 'HIGH':
        print(f"⚠️  Risk Level: 🔴 HIGH")
    elif risk_level == 'MEDIUM':
        print(f"⚠️  Risk Level: 🟡 MEDIUM")
    else:
        print(f"✅ Risk Level: 🟢 LOW")
    
    # Quick buttons
    print("\n📌 Quick Actions:")
    if quick_buttons['quick_add']:
        print("  ⚠️  Quick Add buttons detected")
    if quick_buttons['quick_view']:
        print("  ⚠️  Quick View buttons detected")
    if quick_buttons['quick_buy']:
        print("  ⚠️  Quick Buy buttons detected")
    if quick_buttons['choose_options']:
        print("  ⚠️  'Choose Options' button detected")
    if not any([quick_buttons['quick_add'], quick_buttons['quick_view'], 
                quick_buttons['quick_buy'], quick_buttons['choose_options']]):
        print("  ✅ No quick action buttons detected")
    
    # Bundles
    print("\n📦 Bundle Detection:")
    if bundles['bundles_detected']:
        print(f"  ⚠️  {bundles['bundle_type']} detected")
    else:
        print("  ✅ No bundle features detected")
    
    # Recommendations
    print("\n🎯 Product Recommendations:")
    if recommendations['recommendations_detected']:
        print("  ⚠️  Recommendation sections detected:")
        for rec_type in recommendations['recommendation_types']:
            print(f"     - {rec_type}")
        if recommendations['has_quick_add']:
            print("  ⚠️  Recommendations include Quick Add buttons")
    else:
        print("  ✅ No recommendation sections detected")
    
    # Subscriptions
    print("\n🔄 Subscription Features:")
    if subscriptions['subscription_detected']:
        print("  ⚠️  Subscription functionality detected:")
        for app in subscriptions['subscription_apps']:
            print(f"     - {app}")
    else:
        print("  ✅ No subscription features detected")
    
    # Summary
    print("\n" + "="*60)
    if risk_level == 'HIGH':
        print("⚠️  HIGH RISK - Multiple compatibility issues detected")
        print("   Recommend reaching out to merchant for setup assistance")
    elif risk_level == 'MEDIUM':
        print("⚠️  MEDIUM RISK - Some compatibility concerns")
        print("   Monitor for support tickets, may need custom setup")
    else:
        print("✅ LOW RISK - Minimal compatibility issues")
        print("   Standard setup should work fine")


def check_store(store_url):
    """
    Main function to check a single store.
    
    Args:
        store_url: The Shopify store URL to check
        
    Returns:
        dict with check results for summary table
    """
    print(f"\n🔍 Checking: {store_url}")
    
    # Fetch the homepage
    html = fetch_store_page(store_url)
    
    if not html:
        print("❌ Could not fetch store page. Skipping...")
        return None
    
    # Extract brand name and contact email
    brand_name = extract_brand_name(html)
    contact_email = extract_contact_email(html)
    
    print(f"🏷️  Brand: {brand_name}")
    print(f"📧 Contact: {contact_email}")
    
    # Detect theme
    theme = detect_theme(html)
    
    # Run all checks
    quick_buttons = check_quick_buttons(html)
    bundles = check_bundles(html)
    featured = check_featured_sections(html)
    recommendations = check_recommendations(html)
    subscriptions = check_subscriptions(html)
    risk_level, risk_factors = calculate_risk_level(quick_buttons, bundles, featured, recommendations, subscriptions)
    
    # Generate report
    generate_report(store_url, theme, quick_buttons, bundles, featured, recommendations, subscriptions, risk_level, risk_factors)
    
    # Return results for summary table
    return {
        'url': store_url,
        'brand': brand_name,
        'contact': contact_email,
        'risk_level': risk_level,
        'risk_factors': risk_factors
    }


def generate_summary_table(results):
    """
    Generate a summary table of all checked stores sorted by risk level.
    Auto-adjusts column widths based on terminal size.
    
    Args:
        results: List of dicts with store check results
    """
    if not results:
        return
    
    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    
    # Sort by risk level: HIGH -> MEDIUM -> LOW
    risk_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    sorted_results = sorted(results, key=lambda x: risk_order.get(x['risk_level'], 3))
    
    print("\n" + "="*terminal_width)
    print("📊 SUMMARY - ALL STORES")
    print("="*terminal_width)
    
    # Fixed column widths
    risk_width = 12
    status_width = 15
    
    # Calculate flexible column widths
    # Reserve space for: RISK (12) + STATUS (15) + separators (12)
    reserved = risk_width + status_width + 12
    available = terminal_width - reserved
    
    # Distribute available space
    # Priority: ISSUES gets most space, then STORE, BRAND, CONTACT
    if available >= 150:
        # Wide terminal - generous spacing
        store_width = 35
        brand_width = 30
        contact_width = 35
        issues_width = available - store_width - brand_width - contact_width
    elif available >= 100:
        # Medium terminal
        store_width = 30
        brand_width = 25
        contact_width = 30
        issues_width = available - store_width - brand_width - contact_width
    else:
        # Narrow terminal - minimal spacing
        store_width = max(20, int(available * 0.25))
        brand_width = max(15, int(available * 0.20))
        contact_width = max(20, int(available * 0.25))
        issues_width = available - store_width - brand_width - contact_width
    
    # Ensure minimum widths
    issues_width = max(30, issues_width)
    
    # Print table header
    header = f"{'STORE':<{store_width}} {'BRAND':<{brand_width}} {'CONTACT':<{contact_width}} {'RISK':<{risk_width}} {'STATUS':<{status_width}} {'ISSUES DETECTED'}"
    print(f"\n{header}")
    print("-" * terminal_width)
    
    # Print each store
    for result in sorted_results:
        # Truncate fields to fit widths
        store = result['url']
        if len(store) > store_width - 2:
            store = store[:store_width-2]
        
        brand = result.get('brand', 'Unknown')
        if len(brand) > brand_width - 2:
            brand = brand[:brand_width-2]
        
        contact = result.get('contact', 'No public email found')
        if len(contact) > contact_width - 2:
            contact = contact[:contact_width-2]
        
        risk = result['risk_level']
        
        # Color code risk level
        if risk == 'HIGH':
            risk_display = '🔴 HIGH'
        elif risk == 'MEDIUM':
            risk_display = '🟡 MEDIUM'
        else:
            risk_display = '🟢 LOW'
        
        # Status indicator
        if result.get('uninstalled', False):
            status = '🚫 Uninstalled'
        else:
            status = '✅ Active'
        
        # Format issues - full text, no truncation
        if result['risk_factors']:
            issues = ', '.join(result['risk_factors'])
        else:
            issues = "No issues"
        
        # Print row
        print(f"{store:<{store_width}} {brand:<{brand_width}} {contact:<{contact_width}} {risk_display:<{risk_width}} {status:<{status_width}} {issues}")
    
    # Print summary stats
    print("-" * terminal_width)
    high_count = sum(1 for r in results if r['risk_level'] == 'HIGH')
    medium_count = sum(1 for r in results if r['risk_level'] == 'MEDIUM')
    low_count = sum(1 for r in results if r['risk_level'] == 'LOW')
    uninstalled_count = sum(1 for r in results if r.get('uninstalled', False))
    
    print(f"\nTotal Stores Checked: {len(results)}")
    print(f"  🔴 HIGH RISK: {high_count}")
    print(f"  🟡 MEDIUM RISK: {medium_count}")
    print(f"  🟢 LOW RISK: {low_count}")
    if uninstalled_count > 0:
        print(f"  🚫 UNINSTALLED: {uninstalled_count} (skip outreach)")
    print("\n" + "="*terminal_width + "\n")


def main():
    """
    Main entry point for the script.
    Supports batch processing - paste multiple URLs at once!
    """
    print("="*60)
    print("🛠️  SHOPIFY THEME COMPATIBILITY CHECKER V7")
    print("   For Early Bird Pre-order App")
    print("   Now with: Brand Name + Contact Email + Auto-width Table")
    print("="*60)
    print("\n📝 PASTE ALL STORE URLs & ACTIVITY (one per line)")
    print("   Supports Slack notifications from #early-bird")
    print("   Press ENTER twice when done, or type 'quit' to exit")
    print("="*60 + "\n")
    
    urls = []
    uninstalled_stores = set()  # Track stores that uninstalled
    results = []  # Track results for summary table
    empty_line_count = 0
    
    while True:
        try:
            line = input().strip()
            
            # Check for quit command
            if line.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using the checker!")
                break
            
            # Track empty lines
            if not line:
                empty_line_count += 1
                # Two consecutive empty lines means user is done
                if empty_line_count >= 2:
                    if urls:
                        # Deduplicate URLs while preserving order
                        unique_urls = list(dict.fromkeys(urls))
                        
                        # Show stats
                        print(f"\n✅ Found {len(urls)} activities from {len(unique_urls)} unique store(s)")
                        if uninstalled_stores:
                            print(f"⚠️  {len(uninstalled_stores)} store(s) uninstalled (marked in summary)")
                        print(f"🔍 Checking {len(unique_urls)} store(s)...")
                        print("="*60)
                        
                        for i, url in enumerate(unique_urls, 1):
                            print(f"\n[{i}/{len(unique_urls)}] Processing...")
                            result = check_store(url)
                            if result:
                                # Add uninstall status to result
                                result['uninstalled'] = url in uninstalled_stores
                                results.append(result)
                            
                            # Add separator between stores
                            if i < len(unique_urls):
                                print("\n" + "~"*60)
                        
                        print("\n✅ All stores checked!")
                        
                        # Show summary table
                        generate_summary_table(results)
                    
                    # Reset for next batch
                    urls = []
                    uninstalled_stores = set()
                    results = []
                    empty_line_count = 0
                    print("\n📝 Ready for next batch (or 'quit' to exit):\n")
            else:
                empty_line_count = 0
                
                # Check if this is an uninstall notification
                if 'uninstall from' in line.lower():
                    # Extract URL from uninstall message
                    url_match = re.search(r'\(([^)]+\.myshopify\.com)\)', line)
                    if url_match:
                        uninstalled_url = url_match.group(1)
                        uninstalled_stores.add(uninstalled_url)
                
                # Extract just the URL from Slack format if needed
                # Example: "New install from Store Name (store-url.myshopify.com)!"
                url_match = re.search(r'\(([^)]+\.myshopify\.com)\)', line)
                if url_match:
                    url = url_match.group(1)
                else:
                    # Try to extract any URL-like string
                    url_match = re.search(r'([a-z0-9-]+\.myshopify\.com|[a-z0-9-]+\.[a-z]{2,})', line, re.IGNORECASE)
                    if url_match:
                        url = url_match.group(1)
                    else:
                        # Use the whole line if it looks like a URL
                        url = line
                
                if url:
                    urls.append(url)
        
        except EOFError:
            # End of input
            if urls:
                # Deduplicate URLs while preserving order
                unique_urls = list(dict.fromkeys(urls))
                
                print(f"\n✅ Found {len(urls)} activities from {len(unique_urls)} unique store(s)")
                if uninstalled_stores:
                    print(f"⚠️  {len(uninstalled_stores)} store(s) uninstalled (marked in summary)")
                print(f"🔍 Checking {len(unique_urls)} store(s)...")
                print("="*60)
                
                for i, url in enumerate(unique_urls, 1):
                    print(f"\n[{i}/{len(unique_urls)}] Processing...")
                    result = check_store(url)
                    if result:
                        # Add uninstall status to result
                        result['uninstalled'] = url in uninstalled_stores
                        results.append(result)
                    
                    if i < len(unique_urls):
                        print("\n" + "~"*60)
                
                print("\n✅ All stores checked!")
                
                # Show summary table
                generate_summary_table(results)
            break
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break


if __name__ == "__main__":
    main()
