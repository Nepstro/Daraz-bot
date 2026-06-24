import os
import time
import pandas as pd
from seleniumbase import Driver
import sys
from selenium.common.exceptions import InvalidSessionIdException, NoSuchElementException, TimeoutException, StaleElementReferenceException
import webbrowser
import re
from io import StringIO
import random
from selenium.webdriver.support.ui import WebDriverWait
from difflib import SequenceMatcher

# --- Static Global Settings ---
MAX_PAGES_TO_CRAWL = 15
MIN_RELEVANCE_RATIO = 0.20
Z_SCORE_THRESHOLD = -3.0
ALERT_LOG_FILE = "triggered_glitches_log.csv"

def display_header():
    """Displays the application's ASCII art header and branding."""
    art = r"""
                                                                             
                                                                             
                                                                             
                                ████▒    ██   █████    ██   ██████                      █████░          █   
                                █  ▒█░   ██   █   ▓█   ██       ▓▓                      █   ▒█          █   
                                █   ▒█  ▒██▒  █    █  ▒██▒     ▒█                       █    █  ███   █████ 
                                █    █  ▓▒▒▓  █   ▒█  ▓▒▒▓     █▒                       █   ▒█ █▓ ▓█    █   
                                █    █  █░░█  █████   █░░█    ▓▓                        █████░ █   █    █   
                                █    █  █  █  █  ░█▒  █  █   ▒█     ███    ███    ███   █   ▒█ █   █    █   
                                █   ▒█ ▒████▒ █   ░█ ▒████▒  █▒                         █    █ █   █    █   
                                █  ▒█░ ▓▒  ▒▓ █    █ ▓▒  ▒▓ █▓                          █   ▒█ █▓ ▓█    █░  
                                ████▒  █░  ░█ █    ▒ █░  ░█ ██████                      █████░  ███     ▒██ 
                                                                                                            
                                                                             
                                                                             
    """
    print(art)
    print("="*120)
    print("DARAZ Bot by Nepstro - Deep Catalog Price Anomaly Detector")
    print("https://github.com/Nepstro")
    print(f"Copyright (c) {time.strftime('%Y')}")
    print("\n                                                     --- DISCLAIMER ---")
    print("                          This tool is provided for educational and informational purposes only.")
    print("                          The creator is not responsible for any decisions made based on the data,")
    print("                          financial losses, or any other consequences of using this software.")
    print("                          Always double-check information on the official Daraz website before")
    print("                          making any purchases. Use at your own risk.")
    print("="*120)
    print("\n")

def spinner_sleep(duration, message="", condition_func=None, driver=None):
    """Displays a CLI spinner for a given duration or until a condition is met."""
    keyframes = [
        "_______", "______🚚", "_____🚚_", "____🚚__",
        "___🚚__", "__🚚___", "_🚚____", "🚚_____",
    ]
    start_time = time.time()
    i = 0
    daraz_phrases = [
        "Bargaining with sellers... 🤝",
        "Dodging flash sales... 🏃‍♂️💨",
        "Counting delivery bikes... 🏍️",
        "Looking for 'Machan' deals... 👀",
        "Checking if it's 'original'... 🤔",
        "Convincing the delivery guy it's prepaid... 😅",
        "Adding to cart... then closing the tab. 🙈",
        "Waiting for the OTP that never comes... ⏳",
        "Filtering out the 'for cover' listings... 🕵️‍♀️",
        "Checking if a missing zero made a laptop Rs. 1,500... 🤯",
        "Scanning for decimal point placement disasters... 🧐",
        "Hunting for sellers who confused USD prices with LKR... 🕵️‍♂️",
        "Exploiting coupon codes that accidentally stack... 🤑",
        "Looking for listings where the discount is higher than the price... 💸",
    ]
    funny_message = random.choice(daraz_phrases)
    success = False
    while time.time() - start_time < duration:
        if condition_func and driver:
            try:
                if condition_func(driver):
                    success = True
                    break
            except Exception:
                pass
                
        frame = keyframes[i % len(keyframes)]
        display_message = f"{message} ({funny_message})"
        sys.stdout.write(f'\r{frame} {display_message}')
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    # Clear the line with plenty of space
    sys.stdout.write('\r' + ' ' * 120 + '\r')
    sys.stdout.flush()
    
    if condition_func and driver and not success:
        raise TimeoutException(f"Timed out after {duration} seconds waiting for condition.")

def is_new_alert_csv(title, price):
    """Checks if a given alert already exists in the persistent CSV log."""
    if not os.path.exists(ALERT_LOG_FILE):
        return True
    try:
        df_log = pd.read_csv(ALERT_LOG_FILE)
        if df_log.empty:
            return True
        return not ((df_log["Title"] == title) & (df_log["Listed Price"] == price)).any()
    except pd.errors.EmptyDataError:
        return True

def initialize_alert_log():
    """Ensures a persistent ledger exists to log unique anomalies."""
    if not os.path.exists(ALERT_LOG_FILE):
        df = pd.DataFrame(columns=["Timestamp", "Search Query", "Title", "Listed Price", "Market Median", "URL"])
        df.to_csv(ALERT_LOG_FILE, index=False)

def log_new_alert_csv(query, title, price, median, url):
    """Logs a flagged anomaly to the CSV ledger if it has not been captured previously."""
    df_log = pd.read_csv(ALERT_LOG_FILE)
    if not ((df_log["Title"] == title) & (df_log["Listed Price"] == price)).any():
        new_entry = pd.DataFrame([{
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Search Query": query,
            "Title": title,
            "Listed Price": price,
            "Market Median": median,
            "URL": url
        }])
        df_log = pd.concat([df_log, new_entry], ignore_index=True)
        df_log.to_csv(ALERT_LOG_FILE, index=False)

def get_user_config():
    """Gathers search parameters from the user."""
    config = {}
    
    search_query = input("Enter target product for analysis (or press Enter to quit): ").strip()
    if not search_query:
        return None
    config['search_query'] = search_query
        
    return config

def scrape_all_pages(driver, search_query):
    """Crawls through Daraz catalog pages by scraping visible product elements."""
    formatted_query = search_query.replace(" ", "+")
    all_collected_listings = []
    
    print(f"Opening live catalog stream for: [{search_query}]")

    # Start at the first page
    target_url = f"https://www.daraz.lk/catalog/?q={formatted_query}"
    driver.get(target_url)
    print("Waiting for page to load products...")
    try:
        driver.wait_for_element("div[data-qa-locator='product-item']", timeout=15)
        print("Products loaded.")
    except Exception:
        print("Warning: Timed out waiting for product items to appear. The page might be empty or slow.")

    if "403 Forbidden" in driver.get_page_source() or "captcha" in driver.current_url.lower():
        print("Security challenge screen encountered.")
        input("Solve the CAPTCHA inside the browser window manually, then press Enter here to resume...")

    current_page = 1
    while current_page <= MAX_PAGES_TO_CRAWL:
        print(f"\n--- Processing Catalog Page {current_page} of {MAX_PAGES_TO_CRAWL} ---")

        try:
            # Get the ID of the first item on the page to detect page changes later
            first_item_id = driver.find_element("css selector", "div[data-qa-locator='product-item']").get_attribute('data-item-id')
        except NoSuchElementException:
            print(f"No product items detected on page {current_page}. This might be the end of the results.")
            break

        items_on_page = driver.find_elements("css selector", "div[data-qa-locator='product-item']")
        num_items = len(items_on_page)

        page_items_parsed = 0
        relevant_count = 0
        search_keywords = [kw.lower() for kw in search_query.split() if kw.isalnum()]

        keyframes = [
            "_______", "______🚚", "_____🚚_", "____🚚__",
            "___🚚__", "__🚚___", "_🚚____", "🚚_____",
        ]
        daraz_phrases = [
            "Bargaining with sellers... 🤝",
            "Dodging flash sales... 🏃‍♂️💨",
            "Counting delivery bikes... 🏍️",
            "Looking for 'Machan' deals... 👀",
            "Checking if it's 'original'... 🤔",
            "Convincing the delivery guy it's prepaid... 😅",
            "Adding to cart... then closing the tab. 🙈",
            "Waiting for the OTP that never comes... ⏳",
            "Filtering out the 'for cover' listings... 🕵️‍♀️",
            "Checking if a missing zero made a laptop Rs. 1,500... 🤯",
            "Scanning for decimal point placement disasters... 🧐",
        ]
        funny_message = random.choice(daraz_phrases)

        for i in range(num_items):
            # Print spinner during extraction
            frame = keyframes[i % len(keyframes)]
            display_message = f"Extracting item {i+1}/{num_items}... ({funny_message})"
            sys.stdout.write(f'\r{frame} {display_message}')
            sys.stdout.flush()
            
            try:
                # Re-find the item on each iteration to prevent StaleElementReferenceException
                item = driver.find_elements("css selector", "div[data-qa-locator='product-item']")[i]

                # Scroll the item into view to trigger lazy loading
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)

                link_node = item.find_element("css selector", "a")
                item_url = link_node.get_attribute("href")

                # --- Robust Image Extraction ---
                image_url = ""
                try:
                    img_element = item.find_element("css selector", "img")
                    # Wait for lazy-load: check that src is not a base64 placeholder
                    WebDriverWait(driver, 5).until(lambda d: "http" in img_element.get_attribute("src"))
                    raw_url = img_element.get_attribute("src")
                    # Strip resolution suffixes for high-res version
                    image_url = re.sub(r'_\d+x\d+q\d+.*$', '', raw_url)
                except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                    pass # Image not loaded, URL remains empty

                # --- Robust Data Parsing ---
                # This multi-layered approach ensures the most accurate title is captured.
                # 1. Prioritize the 'title' attribute of the main link.
                title_text = item.find_element("css selector", "a").get_attribute('title').strip()
                
                # 2. If empty, fall back to the image's 'alt' text, which is often a clean title.
                if not title_text:
                    try:
                        title_text = item.find_element("css selector", "img").get_attribute('alt').strip()
                    except NoSuchElementException:
                        pass # No image found, proceed to next fallback

                # 3. As a last resort, parse the visible text.
                if not title_text:
                    lines = item.text.strip().split("\n")
                    for line in lines:
                        cleaned = line.strip()
                        # Filter out common junk text (prices, badges, etc.) to find the title.
                        if cleaned and "Rs." not in cleaned and not cleaned.isdigit() and cleaned not in ["Choice", "Mall", "Free Shipping", "Coins"]:
                            title_text = cleaned
                            break # Assume first valid line is the title

                price_text = item.find_element("css selector", ".ooOxS").text
                clean_price = re.sub(r'[^\d]', '', price_text)

                badge_text = ""
                try:
                    badge_element = item.find_element("css selector", ".Ic-Xb")
                    badge_text = badge_element.text.strip()
                except NoSuchElementException:
                    pass # No badge found

                listed_discount = None
                try:
                    # Scrape the seller's listed discount percentage, if available
                    discount_element = item.find_element("css selector", ".IcOsH")
                    discount_text = discount_element.text.strip() # e.g., "75% Off"
                    discount_match = re.search(r'(\d+)', discount_text)
                    if discount_match:
                        listed_discount = float(discount_match.group(1))
                except NoSuchElementException:
                    pass # No listed discount found
                    
                sold_count = None
                try:
                    sold_element = item.find_element("css selector", "._1cEkb")
                    sold_text = sold_element.text.strip()
                    sold_match = re.search(r'([\d\.]+k?)\s*sold', sold_text, re.IGNORECASE)
                    if sold_match:
                        raw_sold = sold_match.group(1).lower()
                        if 'k' in raw_sold:
                            sold_count = int(float(raw_sold.replace('k', '')) * 1000)
                        else:
                            sold_count = int(raw_sold)
                except NoSuchElementException:
                    pass

                review_count = None
                try:
                    review_element = item.find_element("css selector", ".qzqFw")
                    review_text = review_element.text.strip()
                    review_match = re.search(r'\((\d+)\)', review_text)
                    if review_match:
                        review_count = int(review_match.group(1))
                except NoSuchElementException:
                    pass
                
                location = ""
                try:
                    location_element = item.find_element("css selector", ".oa6ri")
                    location = location_element.text.strip()
                except NoSuchElementException:
                    pass

                all_collected_listings.append({
                    "Title": title_text,
                    "Current Price": float(clean_price),
                    "URL": item_url,
                    "Image URL": image_url,
                    "Badge": badge_text,
                    "Listed Discount": listed_discount,
                    "Sold Count": sold_count,
                    "Review Count": review_count,
                    "Location": location
                })
                page_items_parsed += 1
                
                if any(kw in title_text.lower() for kw in search_keywords):
                    relevant_count += 1
                    
            except (NoSuchElementException, ValueError, StaleElementReferenceException, IndexError):
                # This item might be an ad or have a different structure. Skip it.
                continue

        # Clear the line after loop
        sys.stdout.write('\r' + ' ' * 120 + '\r')
        sys.stdout.flush()

        print(f"Successfully compiled {page_items_parsed} product listings from page {current_page}.")
        
        if page_items_parsed > 0:
            relevance_ratio = relevant_count / page_items_parsed
            print(f"Page Relevance Score: {relevance_ratio*100:.0f}%")
            if relevance_ratio < MIN_RELEVANCE_RATIO and current_page > 1:
                print("Relevance dropped significantly below threshold. Assuming irrelevant accessory section reached. Halting crawl.")
                break

        if current_page < MAX_PAGES_TO_CRAWL:
            try:
                # The selector is updated to target the parent <li> element, which is more robust.
                # The click event is often attached to this container rather than the inner <a> or <svg>.
                next_button = driver.find_element("css selector", ".ant-pagination-next:not(.ant-pagination-disabled)")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                spinner_sleep(1.5, "Preparing for next page...")
                next_button.click()
                
                next_page_num = current_page + 1
                # --- Robust Page Transition Wait ---
                # Reverting to a URL-based wait, as it's more reliable than checking DOM state.
                # It waits for the '&page=' parameter in the URL to update.
                spinner_sleep(
                    duration=15, 
                    message=f"Navigating to page {next_page_num}...", 
                    condition_func=lambda d: f"page={next_page_num}" in d.current_url,
                    driver=driver
                )
                current_page = next_page_num
            except (TimeoutException, NoSuchElementException):
                print("\nCould not find 'Next Page' button or transition failed. Assuming end of search results.")
                break
        else:
            break
            
    return all_collected_listings

def analyze_data(listings, config):
    """Analyzes scraped listings to find the market median and price anomalies using MAD."""
    if not listings:
        print("Zero listings recovered across the entire page crawl path.")
        return None, None, None

    df = pd.DataFrame(listings)
    search_query = config['search_query']

    # --- FUZZY KEYWORD-BASED TITLE FILTER ---
    keywords = [kw for kw in search_query.lower().split() if kw.isalnum()]
    df['Title_Lower'] = df['Title'].str.lower()
    
    def calculate_similarity(title):
        return SequenceMatcher(None, search_query.lower(), title).ratio()
        
    df['Similarity'] = df['Title_Lower'].apply(calculate_similarity)
    
    # Require ALL keywords to match strictly OR high fuzzy similarity
    df_keyword_filtered = df[df['Title_Lower'].apply(lambda title: all(kw in title for kw in keywords)) | (df['Similarity'] > 0.45)].copy()
    
    print(f"\nKeyword/Fuzzy filter applied: Retained {len(df_keyword_filtered)} of {len(df)} items related to '{search_query}'.")

    # --- NEGATIVE KEYWORD FILTER (Accessory Purge) ---
    # Removes common accessory terms unless the user explicitly searched for them.
    negative_keywords = [
        'rack', 'basket', 'cover', 'case', 'liner', 'tray', 'accessories', 'accessory',
        'parts', 'replacement', 'silicone', 'paper', 'film', 'sticker', 'glass',
        'shell', 'tools', 'cleaning', 'protector', 'tempered', 'bracket', 
        'skewer', 'dehydrator', 'mold', 'spare', 'cable', 'charger', 'adapter',
        'makeup', 'powder', 'concealer', 'foundation', 'repair', 'earmuff'
    ]
    
    # Expand list with simple plurals for robustness
    expanded_neg_keywords = set()
    for nkw in negative_keywords:
        expanded_neg_keywords.add(nkw)
        if not nkw.endswith('s'):
            expanded_neg_keywords.add(nkw + 's')
    
    def is_accessory(title):
        t_lower = title.lower()
        search_lower = search_query.lower()
        return any(
            re.search(r'\b' + re.escape(nkw) + r'\b', t_lower)
            for nkw in expanded_neg_keywords 
            if nkw not in search_lower
        )
        
    pre_neg_count = len(df_keyword_filtered)
    df_keyword_filtered = df_keyword_filtered[~df_keyword_filtered['Title_Lower'].apply(is_accessory)].copy()
    print(f"Negative Accessory filter applied: Retained {len(df_keyword_filtered)} of {pre_neg_count} items.")

    if df_keyword_filtered.empty:
        print("No items matched the search criteria (or all were accessories). Analysis cannot proceed.")
        return None, None, None

    # --- AUTOMATIC PRICE FLOOR (Top-Relevance Anchor approach) ---
    # Accessories often overlap with cheap appliances, breaking gap analysis.
    # Instead, we find the "true" product price by taking the median price of the 
    # top items whose titles most identically match the search query.
    df_sorted_by_sim = df_keyword_filtered.sort_values(by='Similarity', ascending=False)
    top_n = max(3, min(20, int(len(df_sorted_by_sim) * 0.15)))
    
    if len(df_sorted_by_sim) < top_n:
        top_relevant_items = df_sorted_by_sim
    else:
        top_relevant_items = df_sorted_by_sim.head(top_n)
        
    anchor_price = top_relevant_items['Current Price'].median()
    
    # Establish floor at 20% of the anchor price. This mathematically purges cheap accessories
    # while allowing massive (up to 80%) real discounts to pass through.
    automatic_price_floor = anchor_price * 0.20
    
    print(f"\nAutomatic Accessory Filter (Top-Relevance):")
    print(f"Detected Anchor Price: Rs. {anchor_price:,.2f}")
    print(f"Established Price Floor: Rs. {automatic_price_floor:,.2f} (20% of Anchor)")
    
    pre_floor_count = len(df_keyword_filtered)
    df_fully_filtered = df_keyword_filtered[df_keyword_filtered['Current Price'] >= automatic_price_floor].copy()
    print(f"Filter applied: Retained {len(df_fully_filtered)} of {pre_floor_count} items above floor.")

    if len(df_fully_filtered) < 3:
        print("Not enough items remaining for statistical anomaly detection. Analysis cannot proceed.")
        return None, None, None

    # --- ROBUST MAD / Z-SCORE ANOMALY DETECTION ---
    print("\nCalculating robust market statistics using Median Absolute Deviation (MAD)...")
    prices = df_fully_filtered["Current Price"]
    median_market_price = prices.median()
    
    abs_dev = (prices - median_market_price).abs()
    mad = abs_dev.median()
    
    if mad == 0:
        mad = prices.std() if prices.std() > 0 else 1.0

    df_fully_filtered['Modified_Z_Score'] = 0.6745 * (prices - median_market_price) / mad
    df_fully_filtered['Discount'] = (((median_market_price - df_fully_filtered['Current Price']) / median_market_price) * 100)
    
    total_records = len(df_fully_filtered)
    
    print(f"\n=== MARKET STATISTICS ===")
    print(f"Total Products Evaluated: {total_records}")
    print(f"Market Median: Rs. {median_market_price:,.2f}")
    print(f"Median Absolute Deviation (MAD): Rs. {mad:,.2f}")
    
    anomalies = df_fully_filtered[df_fully_filtered['Modified_Z_Score'] <= Z_SCORE_THRESHOLD].copy()
    
    return df_fully_filtered, anomalies, median_market_price

def build_html_table(df, config, highlight_identifiers=set()):
    """Builds a clean HTML table string from a DataFrame."""
    table_html = '<table class="table">\n'
    # Headers
    table_html += "  <thead>\n    <tr>\n"
    table_html += '      <th style="width: 8%;">Image</th>\n'
    table_html += '      <th style="width: 25%;">Product Details</th>\n'
    table_html += '      <th style="width: 8%;">Badge</th>\n'
    table_html += '      <th style="width: 10%;">Listed Price (Rs.)</th>\n'
    table_html += '      <th style="width: 10%;">Market Median (Rs.)</th>\n'
    table_html += '      <th style="width: 8%;">Market Discount</th>\n'
    table_html += '      <th style="width: 8%;">Listed Discount</th>\n'
    table_html += '      <th style="width: 8%;">Metrics</th>\n'
    table_html += '      <th style="width: 15%;">Link / Location</th>\n'
    table_html += "    </tr>\n  </thead>\n"
    # Body
    table_html += "  <tbody>\n"
    for _, row in df.iterrows():
        row_identifier = (row['Title'], row['Current Price'])
        highlight_class = ' class="highlight"' if row_identifier in highlight_identifiers else ''
        badge = row.get("Badge", "")
        badge_color = "#007bff" if badge == "Mall" else "#28a745" if badge == "Choice" else "#6c757d"

        table_html += f'    <tr{highlight_class}>\n'
        table_html += f'      <td><img src="{row.get("Image URL", "")}" width="100" style="max-width:100px;"></td>\n'
        # Product Details cell
        details_html = f'<td><strong>{row["Title"]}</strong>'
        if pd.notna(row.get('Modified_Z_Score')) and row.get('Modified_Z_Score', 0) <= Z_SCORE_THRESHOLD:
            confidence_text = ""
            if badge == "Mall":
                confidence_text = " This is a **high-confidence** alert from a Daraz Mall seller."
            details_html += f'<br><p style="color: #dc3545; font-size: 0.9em; margin-top: 5px;">This product is flagged as a statistical anomaly (Z-Score: {row["Modified_Z_Score"]:.1f})! It is listed at a <strong>{row["Discount"]:.1f}% discount</strong> compared to the market median.{confidence_text}</p>'
        details_html += '</td>'
        table_html += f'      {details_html}\n'
        table_html += f'      <td><span style="color: {badge_color}; font-weight: bold;">{badge}</span></td>\n'
        table_html += f'      <td style="font-weight: bold; color: #28a745;">{row["Current Price"]:,.2f}</td>\n'
        median_str = f"{row.get('Market Median', ''):,.2f}" if pd.notna(row.get('Market Median')) else "N/A"
        market_discount_str = f"{row.get('Discount', ''):.1f}%" if pd.notna(row.get('Discount')) else "N/A"
        listed_discount_str = f"{row.get('Listed Discount'):.0f}%" if pd.notna(row.get('Listed Discount')) else "N/A"
        
        sold_str = f"{row.get('Sold Count')} sold" if pd.notna(row.get('Sold Count')) else "0 sold"
        review_str = f"({row.get('Review Count')} revs)" if pd.notna(row.get('Review Count')) else "(0 revs)"
        loc_str = row.get("Location", "Unknown") if pd.notna(row.get("Location")) and row.get("Location", "") else "Unknown"
        
        table_html += f'      <td>{median_str}</td>\n'
        table_html += f'      <td>{market_discount_str}</td>\n'
        table_html += f'      <td>{listed_discount_str}</td>\n'
        table_html += f'      <td><span style="font-size:0.9em; color:#495057;">{sold_str}<br>{review_str}</span></td>\n'
        table_html += f'      <td><a href="{row["URL"]}" target="_blank">View Product</a><br><span style="font-size:0.85em; color:#868e96;">📍 {loc_str}</span></td>\n'
        table_html += "    </tr>\n"
    table_html += "  </tbody>\n</table>"
    return table_html

def generate_report(df_to_report, current_anomalies, median_price, config):
    """Generates a self-contained HTML reports with historical and new alerts."""
    search_query = config['search_query']
    df_sorted = df_to_report.sort_values(by="Current Price", ascending=True).reset_index(drop=True)

    # --- Generate a unique filename to avoid overwriting previous reports ---
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        
    base_filename = f"daraz_{search_query.lower().replace(' ', '_')}_deep.html"
    base_out_file = os.path.join(reports_dir, base_filename)
    out_file = base_out_file
    counter = 1
    # If the file exists, find a new name like '..._1.html', '..._2.html'
    while os.path.exists(out_file):
        name, ext = os.path.splitext(base_out_file)
        out_file = f"{name}_{counter}{ext}"
        counter += 1

    # --- Isolate *truly* new anomalies for highlighting and console output ---
    new_anomaly_rows = []
    if not current_anomalies.empty:
        for _, row in current_anomalies.iterrows():
            # Check against the persistent CSV log to determine if an anomaly is "new"
            if is_new_alert_csv(row["Title"], row["Current Price"]):
                new_anomaly_rows.append(row)
    
    new_anomalies_df = pd.DataFrame(new_anomaly_rows, columns=current_anomalies.columns) if new_anomaly_rows else pd.DataFrame()

    # The "Priority Alerts Log" in the HTML report will show all anomalies from the current scan.
    all_priority_alerts_df = current_anomalies.copy()
    if not all_priority_alerts_df.empty:
        all_priority_alerts_df['Market Median'] = median_price
        all_priority_alerts_df['Discount'] = (((median_price - all_priority_alerts_df['Current Price']) / median_price) * 100)

    # Create a set of identifiers for *new* anomalies to use for highlighting in the main table
    new_anomaly_identifiers = set()
    if not new_anomalies_df.empty:
        new_anomaly_identifiers = set(zip(new_anomalies_df['Title'], new_anomalies_df['Current Price']))
        # Add context to the new anomalies dataframe for the build_html_table function
        new_anomalies_df['Market Median'] = median_price
        new_anomalies_df['Discount'] = (((median_price - new_anomalies_df['Current Price']) / median_price) * 100)

    # --- Generate the priority HTML section for new alerts ---
    priority_html_section = ""
    if not all_priority_alerts_df.empty:
        # Ensure all required columns exist, filling with NaN if necessary
        if 'Image URL' not in all_priority_alerts_df.columns:
            all_priority_alerts_df['Image URL'] = ''
        for col in ['Market Median', 'Discount']:
            if col not in all_priority_alerts_df.columns:
                all_priority_alerts_df[col] = pd.NA

        priority_alerts_table = build_html_table(all_priority_alerts_df, config, highlight_identifiers=new_anomaly_identifiers)
        priority_html_section = f"""
        <h2>🚨 Priority Alerts Log 🚨</h2>
        <p>Found {len(all_priority_alerts_df)} deal(s) in this scan that meet your criteria.</p>
        {priority_alerts_table}
        <br><hr><br>
        <h2>Full Product Index</h2>
        <p>The full list of all products found is below. Deals are highlighted for context.</p>
        """

    # --- Generate the main HTML table ---
    # Add context columns to the main dataframe for consistent table structure
    df_sorted_detailed = df_sorted.copy()
    df_sorted_detailed['Market Median'] = median_price
    df_sorted_detailed['Discount'] = (((median_price - df_sorted_detailed['Current Price']) / median_price) * 100)
    main_html_table = build_html_table(df_sorted_detailed, config, highlight_identifiers=new_anomaly_identifiers)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Daraz Analysis for "{search_query}"</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 2em; background-color: #f8f9fa; color: #212529; }}
            h1, h2 {{ color: #007bff; border-bottom: 2px solid #dee2e6; padding-bottom: 0.5em; }}
            p {{ font-size: 1.1em; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 25px; box-shadow: 0 0 20px rgba(0, 0, 0, 0.1); }}
            .table th, .table td {{ padding: 15px; border: 1px solid #dee2e6; text-align: left; vertical-align: middle; }}
            .table th {{ background-color: #343a40; color: white; font-weight: 600; }}
            .table tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .table tr:hover {{ background-color: #e9ecef; }}
            a {{ color: #007bff; font-weight: 500; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            tr.highlight {{ background-color: #fff3cd !important; }}
            hr {{ border: 0; border-top: 1px solid #dee2e6; margin: 2em 0; }}
        </style>
    </head>
    <body>
        <h1>Daraz Deep Search Analysis: {search_query}</h1>
        <p><strong>Report Generated:</strong> {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        {priority_html_section}
        {main_html_table}
            <br>
            <div style="text-align: center; font-size: 0.9em; color: #6c757d; margin-top: 2em;">
                <p><strong>Disclaimer:</strong> This report was generated automatically. All data is for informational purposes only. The creator is not responsible for any inaccuracies, financial losses, or decisions made based on this report. Always verify details on the official Daraz website before making a purchase.</p>
            </div>
            <footer>
                <p style="text-align:center; font-size:0.9em; color:#6c757d;">
                    &copy; {time.strftime('%Y')} DARAZ Bot by <a href="https://github.com/Nepstro" target="_blank">Nepstro</a>
                </p>
            </footer>
    </body>
    </html>
    """
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nFull deep-sorted index list written to: {out_file}")

    try:
        webbrowser.open(f'file://{os.path.realpath(out_file)}')
        print(f"Automatically opening {out_file} in your default browser.")
    except Exception as e:
        print(f"Could not automatically open the report file: {e}")
    
    # --- Console Output Section ---
    print("\n🚨🚨🚨 DEEP-CRAWL ALERT VERIFICATION 🚨🚨🚨")
    if not current_anomalies.empty:
        print(f"Found {len(current_anomalies)} critical pricing drops below the threshold.")
        if not new_anomalies_df.empty:
            print(f"Of those, {len(new_anomalies_df)} are NEW discoveries since the last scan!")
            for _, row in new_anomalies_df.iterrows():
                # Log to the persistent CSV file
                log_new_alert_csv(search_query, row['Title'], row['Current Price'], median_price, row['URL'])

                print(f"\n[NEW PRIORITY ALERT RECORDED]")
                print(f"Product: {row['Title']}")
                print(f"Glitch Price: Rs. {row['Current Price']:,} (Normal Market Value: Rs. {median_price:,})")
                print(f"Direct Link: {row['URL']}")
                print("-" * 60)
        else:
            print("No new alerts found in this scan. All identified anomalies were previously logged in the HTML report.")
    else:
        print("No critical pricing anomalies identified across the deep catalog index search.")

def run_deep_search():
    """Main orchestrator for the Daraz deep search bot."""
    display_header()
    initialize_alert_log()
    
    print("Keep the opened browser and wait for the magic to happen...")
    driver = Driver(uc=True, headless=False)
    # Instead of minimizing (which can pause browser JS), we move the window off-screen.
    # This keeps it invisible but fully active, ensuring the script runs at full speed.
    driver.set_window_position(-3000, 0)
    
    try:
        while True:
            config = get_user_config()
            if not config:
                print("\nNo search query entered. Exiting.")
                break  # Exit the while loop

            print(f"\n[CONFIG ACTIVATED] Initiating automated deep search for '{config['search_query']}'")
            
            try:
                all_listings = scrape_all_pages(driver, config['search_query'])
            except InvalidSessionIdException:
                print("\nBrowser session lost. Starting a new one and retrying the search...")
                try:
                    driver.quit() # Attempt to clean up the old one
                except Exception: pass
                driver = Driver(uc=True, headless=False)
                # Move the new window off-screen as well
                driver.set_window_position(-3000, 0)
                all_listings = scrape_all_pages(driver, config['search_query'])
            
            df_processed, anomalies, median_price = analyze_data(all_listings, config)
            
            if df_processed is not None:
                generate_report(df_processed, anomalies, median_price, config)
            
            print("\n" + "="*60)
            print("Search complete. Ready for next query.")
            print("="*60)
            
    finally:
        print("\nAll searches complete. Shutting down browser context.")
        if 'driver' in locals() and driver and driver.session_id:
            try:
                driver.quit()
            except Exception:
                # Ignore errors on quit, session might be dead already
                pass

if __name__ == "__main__":
    run_deep_search()