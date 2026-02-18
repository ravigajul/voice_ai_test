#!/usr/bin/env python3
"""
Order Verification Unit
Reads the Order Complete screen via Appium and verifies items match what was
ordered during the voice interaction.

Screens handled:
  - ORDER COMPLETE (auto-detected)
      → Overview tab  : order number, item count, payment card, totals
      → Order Details : individual items scrolled fully and compared vs log
  - Cart screen (fallback)
      → original item-list comparison

Usage:
  - Standalone: python verify_order.py (active Appium session, correct screen visible)
  - From code:  verify_order(driver, expected_items=["Large pepperoni pizza", "Garlic knots"])
  - From log:   verify_order(driver, log_file="logs/test_run_20260209_162033.txt")
"""
from appium.webdriver.common.appiumby import AppiumBy
from src.appium_driver import AppiumDriver
from src.ollama_client import OllamaClient
import os
import glob
import re
import time
import json
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Screen detection
# ─────────────────────────────────────────────────────────────────────────────

def wait_for_order_complete_screen(driver, timeout=180, poll_interval=5):
    """
    Poll until the ORDER COMPLETE screen appears.

    The app takes a few minutes to process and display the ORDER COMPLETE screen
    after the voice agent confirms the order. This function waits patiently.

    Args:
        driver:        AppiumDriver instance
        timeout:       max seconds to wait (default 180 = 3 minutes)
        poll_interval: seconds between each check (default 5)

    Returns:
        True if ORDER COMPLETE appeared within timeout, False otherwise
    """
    print(f"\n   ⏳ Waiting for ORDER COMPLETE screen (up to {timeout}s)...")
    elapsed = 0
    while elapsed < timeout:
        driver.driver.implicitly_wait(0)
        try:
            found = driver.driver.find_elements(
                AppiumBy.XPATH,
                "//*[@text='ORDER COMPLETE' or @content-desc='ORDER COMPLETE']",
            )
        except Exception:
            found = []
        finally:
            driver.driver.implicitly_wait(10)

        if found:
            print(f"   ✅ ORDER COMPLETE screen detected after {elapsed}s")
            driver.take_screenshot("order_complete_screen")
            return True

        print(f"   ... still waiting ({elapsed}s elapsed)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"   ❌ ORDER COMPLETE screen did not appear within {timeout}s")
    return False


def detect_screen(driver):
    """
    Detect whether the current screen is ORDER COMPLETE or the cart.

    Returns:
        "order_complete" or "cart"
    """
    driver.driver.implicitly_wait(0)
    try:
        matches = driver.driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='ORDER COMPLETE' or @content-desc='ORDER COMPLETE']",
        )
        return "order_complete" if matches else "cart"
    except Exception:
        return "cart"
    finally:
        driver.driver.implicitly_wait(10)


# ─────────────────────────────────────────────────────────────────────────────
# Screen scraping helpers
# ─────────────────────────────────────────────────────────────────────────────

def scrape_screen_texts(driver, screenshot_name=None):
    """
    Collect all visible text and content-desc strings from the current screen
    (single viewport — no scrolling).

    Returns:
        list of unique non-empty strings
    """
    texts = []
    seen = set()

    for xpath, attr in [("//*[@text != '']", "text"), ("//*[@content-desc != '']", "content-desc")]:
        try:
            time.sleep(1)
            for el in driver.driver.find_elements(AppiumBy.XPATH, xpath):
                try:
                    val = el.get_attribute(attr)
                    if val and val.strip() and val.strip() not in seen:
                        texts.append(val.strip())
                        seen.add(val.strip())
                except Exception:
                    continue
        except Exception as e:
            print(f"   ⚠️  Error scraping {attr}: {e}")

    if screenshot_name:
        try:
            driver.take_screenshot(screenshot_name)
            print(f"   📸 Screenshot saved: {screenshot_name}")
        except Exception:
            pass

    return texts


def scrape_full_page_texts(driver, screenshot_name=None, max_scrolls=8):
    """
    Collect all text on a scrollable screen by scrolling down until no new
    content appears. Captures items that are off-screen on first load.

    Uses mobile:swipeGesture with a safe bounding box (never exceeds screen height).

    Args:
        driver:          AppiumDriver instance
        screenshot_name: if set, saves a screenshot after initial scrape
        max_scrolls:     safety cap on scroll iterations

    Returns:
        list of unique non-empty strings from the entire page
    """
    all_texts = set()

    # Collect initial visible content and take screenshot
    initial = scrape_screen_texts(driver, screenshot_name=screenshot_name)
    all_texts.update(initial)
    print(f"   Visible texts before scrolling: {len(all_texts)}")

    size = driver.driver.get_window_size()
    scroll_params = {
        "left": 0,
        "top": int(size["height"] * 0.30),   # start 30% from top
        "width": size["width"],
        "height": int(size["height"] * 0.40), # 40% height — safely within bounds
        "direction": "up",
        "percent": 0.8,
    }

    for scroll_num in range(1, max_scrolls + 1):
        driver.driver.execute_script("mobile: swipeGesture", scroll_params)
        time.sleep(1)

        new_texts = scrape_screen_texts(driver)
        new_count = len(all_texts)
        all_texts.update(new_texts)

        added = len(all_texts) - new_count
        print(f"   Scroll {scroll_num}: +{added} new text elements (total {len(all_texts)})")

        if added == 0:
            print(f"   No new content after scroll {scroll_num} — reached end of page")
            break

    return list(all_texts)


def click_show_details(driver):
    """
    Click all 'Show Details' expand buttons on the Order Details tab so that
    per-item quantities and customisations become visible before scraping.
    Safe to call even when no such buttons exist.
    """
    locators = [
        (AppiumBy.XPATH, "//*[@text='Show Details']"),
        (AppiumBy.XPATH, "//*[contains(@text,'Show Details')]"),
        (AppiumBy.XPATH, "//*[contains(@content-desc,'Show Details')]"),
    ]
    driver.driver.implicitly_wait(0)
    clicked = 0
    try:
        for by, value in locators:
            elements = driver.driver.find_elements(by, value)
            for el in elements:
                try:
                    el.click()
                    clicked += 1
                    time.sleep(0.5)
                except Exception:
                    pass
            if clicked:
                break  # found and clicked — no need to try other locators
    finally:
        driver.driver.implicitly_wait(10)

    if clicked:
        print(f"   ✅ Expanded {clicked} 'Show Details' section(s)")
        time.sleep(1)  # let the UI settle after expansion
    else:
        print("   ℹ️  No 'Show Details' buttons found — items may already be expanded")


def _click_tab(driver, tab_name, locators, retries=3, wait_between=2):
    """
    Generic helper: click a named tab and wait for it to become active.

    Checks whether we are already on the tab (by looking for a tab-specific
    sentinel element) before clicking, so the function is safe to call even
    when the tab is already selected.

    Args:
        driver:       AppiumDriver instance
        tab_name:     human-readable name used in log messages
        locators:     list of (AppiumBy, value) tuples tried in order
        retries:      max click attempts
        wait_between: seconds between retry attempts

    Returns:
        True if the tab was clicked (or was already active), False otherwise
    """
    for attempt in range(1, retries + 1):
        driver.driver.implicitly_wait(0)
        try:
            for by, value in locators:
                elements = driver.driver.find_elements(by, value)
                if elements:
                    elements[0].click()
                    time.sleep(2)
                    print(f"   ✅ Navigated to '{tab_name}' tab (attempt {attempt})")
                    return True
        finally:
            driver.driver.implicitly_wait(10)

        print(f"   ⚠️  '{tab_name}' tab not found (attempt {attempt}/{retries})"
              f" — retrying in {wait_between}s...")
        time.sleep(wait_between)

    print(f"   ❌ '{tab_name}' tab not found after {retries} attempts")
    return False


def click_overview_tab(driver, retries=3, wait_between=2):
    """
    Navigate to the 'Overview' tab on the Order Complete screen.

    Returns:
        True if clicked successfully, False otherwise
    """
    locators = [
        (AppiumBy.XPATH, "//*[@text='Overview']"),
        (AppiumBy.ACCESSIBILITY_ID, "Overview"),
        (AppiumBy.XPATH, "//*[contains(@text,'Overview')]"),
        (AppiumBy.XPATH, "//*[contains(@content-desc,'Overview')]"),
    ]
    return _click_tab(driver, "Overview", locators, retries, wait_between)


def click_order_details_tab(driver, retries=3, wait_between=2):
    """
    Navigate to the 'Order Details' tab on the Order Complete screen.

    Returns:
        True if clicked successfully, False otherwise
    """
    locators = [
        (AppiumBy.XPATH, "//*[@text='Order Details']"),
        (AppiumBy.ACCESSIBILITY_ID, "Order Details"),
        (AppiumBy.XPATH, "//*[contains(@text,'Order Details')]"),
        (AppiumBy.XPATH, "//*[contains(@content-desc,'Order Details')]"),
    ]
    return _click_tab(driver, "Order Details", locators, retries, wait_between)


# ─────────────────────────────────────────────────────────────────────────────
# Order Complete verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_order_complete(driver, expected_items, ollama):
    """
    Verify the ORDER COMPLETE screen — Overview tab and Order Details tab.

    Steps:
      1. Scrape Overview tab  → order number, item count, payment card, totals
      2. Click Order Details  → full-page scroll to capture all items
      3. Compare items against expected_items via Ollama

    Args:
        driver:         AppiumDriver with ORDER COMPLETE screen visible
        expected_items: list of expected item strings from conversation log
        ollama:         OllamaClient instance

    Returns:
        dict with keys: passed, score, matched_items, missing_items,
                        extra_items, reasoning, overview
    """
    print("\n" + "=" * 60)
    print("ORDER COMPLETE VERIFICATION")
    print("=" * 60)

    # ── OVERVIEW TAB ──────────────────────────────────────────────
    print("\n── Overview Tab ──")
    clicked_overview = click_overview_tab(driver)
    if not clicked_overview:
        print("   ⚠️  'Overview' tab click failed — scraping current screen anyway.")

    overview_texts = scrape_screen_texts(driver, screenshot_name="order_complete_overview")
    print(f"   Scraped {len(overview_texts)} text elements from Overview")
    for i, t in enumerate(overview_texts, 1):
        print(f"      [{i}] {t}")

    overview = _parse_overview(overview_texts)
    print(f"\n   Parsed Overview:")
    print(f"      Order #    : {overview.get('order_number', 'not found')}")
    print(f"      Item count : {overview.get('item_count', 'not found')}")
    print(f"      Payment    : {overview.get('payment', 'not found')}")
    print(f"      Total      : {overview.get('order_total', 'not found')}")

    # ── ORDER DETAILS TAB ─────────────────────────────────────────
    print("\n── Order Details Tab ──")
    clicked_details = click_order_details_tab(driver)

    if not clicked_details:
        print("   ⚠️  'Order Details' tab click failed — scraping current screen anyway.")

    # Expand any collapsed item rows so quantities are visible before scraping
    click_show_details(driver)

    # Scroll through the full tab so off-screen items are not missed
    details_texts = scrape_full_page_texts(
        driver, screenshot_name="order_complete_details"
    )
    print(f"   Total text elements collected (all scrolls): {len(details_texts)}")
    for i, t in enumerate(details_texts, 1):
        print(f"      [{i}] {t}")

    # ── COMPARE ITEMS ─────────────────────────────────────────────
    print("\n── Comparing Items vs Expected Order ──")
    order_data = {
        "raw_texts": details_texts,
        "content_descs": [],
        "clickable_elements": [],
    }
    item_results = compare_order_items(order_data, expected_items, ollama)

    # Attach overview summary
    item_results["overview"] = overview

    # Note payment card in reasoning (informational only — not a failure criterion)
    payment = overview.get("payment", "")
    if payment and "0007" not in payment and "007" not in payment:
        item_results["reasoning"] = (
            item_results.get("reasoning", "") +
            f" | Note: payment card shown as '{payment}' (expected ...007)"
        )

    return item_results


def _parse_overview(texts):
    """
    Extract structured fields from the Overview tab raw text strings.

    Returns:
        dict with order_number, item_count, payment, order_total, order_total_amount
    """
    overview = {}

    for t in texts:
        t_lower = t.lower()
        if t_lower.startswith("order #") or t_lower.startswith("order#"):
            overview["order_number"] = t.strip()
        elif t_lower.endswith("items") or t_lower.endswith("item"):
            overview["item_count"] = t.strip()
        elif "credit card" in t_lower or "0007" in t or "...0007" in t:
            overview["payment"] = t.strip()
        elif t_lower.startswith("order total"):
            overview["order_total"] = t.strip()
        elif (
            t.startswith("$")
            and "order_total" in overview
            and "order_total_amount" not in overview
        ):
            overview["order_total_amount"] = t.strip()

    # Fallback payment detection
    if "payment" not in overview:
        for t in texts:
            if "payment by credit card" in t.lower() or "credit card" in t.lower():
                overview["payment"] = t.strip()
                break

    return overview


# ─────────────────────────────────────────────────────────────────────────────
# Cart screen scraping (fallback)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_cart_items(driver):
    """
    Scrape all visible cart items from the cart screen.

    Returns:
        dict with raw_texts, content_descs, clickable_elements
    """
    print("\n" + "=" * 60)
    print("SCRAPING CART SCREEN")
    print("=" * 60)

    result = {"raw_texts": [], "content_descs": [], "clickable_elements": []}

    print("\n   Collecting visible text elements...")
    for attempt in range(3):
        try:
            time.sleep(1)
            for elem in driver.driver.find_elements(AppiumBy.XPATH, "//*[@text]"):
                try:
                    text = elem.get_attribute("text")
                    if text and text.strip():
                        result["raw_texts"].append(text.strip())
                except Exception:
                    continue
            break
        except Exception as e:
            if attempt < 2:
                print(f"   ⚠️  Retry {attempt + 1}/3 collecting text elements...")
                time.sleep(2)
            else:
                print(f"   ⚠️  Error after 3 attempts: {e}")

    print(f"   Found {len(result['raw_texts'])} text elements")
    for i, t in enumerate(result["raw_texts"], 1):
        print(f"      [{i}] {t}")

    print("\n   Collecting content-desc attributes...")
    try:
        for elem in driver.driver.find_elements(AppiumBy.XPATH, "//*[@content-desc]"):
            desc = elem.get_attribute("content-desc")
            if desc and desc.strip():
                result["content_descs"].append(desc.strip())
    except Exception as e:
        print(f"   ⚠️  Error collecting content-desc: {e}")

    print(f"   Found {len(result['content_descs'])} content-desc elements")

    try:
        driver.take_screenshot("cart_verification")
        print("   📸 Cart screenshot saved")
    except Exception as e:
        print(f"   ⚠️  Screenshot failed: {e}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Log extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_expected_from_log(log_file, ollama=None):
    """
    Parse a conversation log and use Ollama to extract the final confirmed items.

    Returns:
        list of expected item strings
    """
    print("\n" + "=" * 60)
    print("EXTRACTING EXPECTED ITEMS FROM CONVERSATION LOG")
    print("=" * 60)

    if not os.path.isfile(log_file):
        print(f"   ❌ Log file not found: {log_file}")
        return []

    with open(log_file, "r") as f:
        transcript = f.read()

    print(f"   📄 Loaded log: {log_file}")
    print(f"   📏 Transcript length: {len(transcript)} chars")

    if not ollama:
        ollama = OllamaClient()

    prompt = f"""Read this conversation transcript between a customer (Ravi) and a pizza ordering agent.
Extract ONLY the final confirmed order items. Include quantity, size, and item name for each.

Transcript:
---
{transcript}
---

Respond in JSON format:
{{
  "items": [
    "quantity size item_name",
    ...
  ]
}}

If no clear order was placed, return {{"items": []}}"""

    system = "You are a precise order extraction system. Extract only confirmed/final order items from conversation transcripts. Output valid JSON only."

    print("   🤖 Asking Ollama to extract order items...")
    response = ollama.generate(prompt, system=system)

    try:
        if "{" in response:
            json_start = response.index("{")
            json_end = response.rindex("}") + 1
            parsed = json.loads(response[json_start:json_end])
            items = parsed.get("items", [])
            print(f"   ✅ Extracted {len(items)} expected items:")
            for i, item in enumerate(items, 1):
                print(f"      [{i}] {item}")
            return items
        else:
            print(f"   ⚠️  No JSON in Ollama response: {response[:100]}")
            return []
    except (json.JSONDecodeError, ValueError) as e:
        print(f"   ❌ Failed to parse Ollama response: {e}")
        print(f"      Raw response: {response[:200]}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Item comparison
# ─────────────────────────────────────────────────────────────────────────────

# ── Keyword-matching helpers (no LLM) ────────────────────────────────────────

# Normalise size abbreviations so "lg" == "large", etc.
_SIZE_ALIASES = {
    "lg": "large", "lrg": "large",
    "md": "medium", "med": "medium",
    "sm": "small",
    "xl": "xlarge",
}

# Words that carry no useful signal for item matching
_STOP_WORDS = {
    "a", "an", "the", "with", "and", "or", "of", "for", "on", "in",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "one", "two", "three", "four", "five",
    "order",  # "1 Order of Breadsticks" — "order" means serving, not product
    "pizza",  # too generic — present in almost every screen line
}


def _clean(text):
    """Lowercase and strip non-alphanumeric characters."""
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower())


def _keywords(text):
    """Return meaningful, normalised tokens from a text string."""
    return [_SIZE_ALIASES.get(w, w) for w in _clean(text).split()
            if w and w not in _STOP_WORDS]


def _token_match(kw, screen_token_set):
    """
    Check if a keyword matches any screen token, with simple plural/singular
    handling so 'breadsticks' matches 'breadstick' and vice versa.
    """
    if kw in screen_token_set:
        return True
    # plural → singular: "breadsticks" → "breadstick"
    if kw.endswith("s") and kw[:-1] in screen_token_set:
        return True
    # singular → plural: "breadstick" → "breadsticks"
    if kw + "s" in screen_token_set:
        return True
    return False


def _item_found_in_screen(expected_item, screen_token_set, screen_combined):
    """
    Return True if the expected item is represented on the order screen.

    Primary check  : ≥60 % of the item's keywords match screen tokens
                     (with basic singular/plural normalisation).
    Secondary check: the item's keyword sequence is a substring of the
                     concatenated screen text.
    """
    kws = _keywords(expected_item)
    if not kws:
        return True  # nothing meaningful to check — assume present

    found = sum(1 for kw in kws if _token_match(kw, screen_token_set))
    ratio = found / len(kws)

    kw_seq = " ".join(kws)

    return ratio >= 0.6 or kw_seq in screen_combined


def compare_order_items(order_data, expected_items, ollama=None):
    """
    Deterministically compare scraped order-screen text against expected items
    using keyword matching.  No LLM is used — results are reproducible and
    cannot hallucinate items.

    Args:
        order_data:     dict with raw_texts / content_descs (from scrape functions)
        expected_items: list of expected item strings from the conversation log
        ollama:         unused; kept for call-site compatibility

    Returns:
        dict with passed, score, matched_items, missing_items, extra_items, reasoning
    """
    print("\n" + "=" * 60)
    print("COMPARING ORDER ITEMS VS EXPECTED")
    print("=" * 60)

    if not expected_items:
        print("   ⚠️  No expected items provided — skipping comparison")
        return {
            "passed": False,
            "score": 0,
            "matched_items": [],
            "missing_items": [],
            "extra_items": [],
            "reasoning": "No expected items to compare against",
        }

    # Filter out UI noise — keep only item-relevant text
    UI_NOISE = {
        "scrim", "remove all", "remove", "more sauce?",
        "add extra cheese", "subtotal", "tax", "make it large",
        "order complete", "overview", "order details", "view rewards",
        "papa rewards", "get directions", "menu", "cart", "home",
        "deals", "profile", "rewards",
    }

    all_order_text = []
    for text in order_data.get("raw_texts", []) + order_data.get("content_descs", []):
        lower = text.lower().strip()
        if any(noise in lower for noise in UI_NOISE):
            continue
        # Skip bare price entries ("$X.XX")
        if lower.startswith("$") and lower.replace("$", "").replace(".", "").isdigit():
            continue
        all_order_text.append(text)

    # Build lookup structures from screen text
    screen_token_set = set()
    for text in all_order_text:
        for word in _clean(text).split():
            screen_token_set.add(_SIZE_ALIASES.get(word, word))
    screen_combined = " ".join(_clean(t) for t in all_order_text)

    print(f"   📋 Expected items: {expected_items}")
    print(f"   🧾 Order text elements after noise filter: {len(all_order_text)}")
    print(f"   🔍 Screen tokens: {len(screen_token_set)}")

    matched_items = []
    missing_items = []

    for item in expected_items:
        kws = _keywords(item)
        found_count = sum(1 for kw in kws if kw in screen_token_set)
        ratio = round(found_count / len(kws), 2) if kws else 1.0
        hit = _item_found_in_screen(item, screen_token_set, screen_combined)
        print(f"   {'✅' if hit else '❌'} '{item}' — keywords {kws}, "
              f"found {found_count}/{len(kws)} ({ratio:.0%})")
        if hit:
            matched_items.append(item)
        else:
            missing_items.append(item)

    total = len(expected_items)
    score = int(100 * len(matched_items) / total) if total else 0
    passed = score >= 80

    reasoning_parts = [
        f"Keyword matching: {len(matched_items)}/{total} expected items found on screen."
    ]
    if missing_items:
        reasoning_parts.append(f"Not found: {', '.join(missing_items)}.")

    return {
        "passed": passed,
        "score": score,
        "matched_items": matched_items,
        "missing_items": missing_items,
        "extra_items": [],   # deterministic check; extra-item detection needs LLM
        "reasoning": " ".join(reasoning_parts),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

def print_report(results, log_filepath=None):
    """
    Print verification results and optionally save to log file.
    """
    print("\n" + "=" * 60)
    print("ORDER VERIFICATION REPORT")
    print("=" * 60)

    passed = results.get("passed", False)
    score = results.get("score", 0)
    print(f"\n   RESULT: {'PASSED' if passed else 'FAILED'} (Score: {score}/100)")

    matched = results.get("matched_items", [])
    missing = results.get("missing_items", [])
    extra   = results.get("extra_items", [])

    if matched:
        print(f"\n   Matched Items ({len(matched)}):")
        for item in matched:
            print(f"      [PASS] {item}")

    if missing:
        print(f"\n   Missing Items ({len(missing)}):")
        for item in missing:
            print(f"      [FAIL] {item}")

    if extra:
        print(f"\n   Unexpected Items ({len(extra)}):")
        for item in extra:
            print(f"      [WARN] {item}")

    overview = results.get("overview")
    if overview:
        print(f"\n   Order Overview:")
        for key, label in [
            ("order_number",      "Order #   "),
            ("item_count",        "Item count"),
            ("payment",           "Payment   "),
            ("order_total",       "Total line"),
            ("order_total_amount","Total amt "),
        ]:
            if overview.get(key):
                print(f"      {label} : {overview[key]}")

    reasoning = results.get("reasoning", "")
    if reasoning:
        print(f"\n   Reasoning: {reasoning}")

    print("\n" + "=" * 60)

    if log_filepath:
        try:
            with open(log_filepath, "w") as f:
                f.write("Order Verification Report\n")
                f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Result: {'PASSED' if passed else 'FAILED'} (Score: {score}/100)\n")
                f.write("-" * 40 + "\n\n")
                f.write(json.dumps(results, indent=2))
                f.write("\n")
            print(f"   📝 Report saved to: {log_filepath}")
        except Exception as e:
            print(f"   ⚠️  Failed to save report: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def verify_order(driver, expected_items=None, log_file=None):
    """
    Main verification entry point.

    Auto-detects the current screen:
      - ORDER COMPLETE → Overview tab (order #, payment, totals)
                         + Order Details tab (full-page scroll, all items)
      - Cart screen    → original cart item verification

    Args:
        driver:         AppiumDriver instance (session open, correct screen visible)
        expected_items: list of expected item strings; if None, extracted from log_file
        log_file:       path to conversation log file

    Returns:
        dict with verification results (passed, score, matched/missing/extra items,
        and 'overview' key when on the ORDER COMPLETE screen)
    """
    ollama = OllamaClient()

    # Resolve expected items
    if not expected_items and log_file:
        expected_items = extract_expected_from_log(log_file, ollama)
    elif not expected_items:
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        log_files = sorted(glob.glob(os.path.join(logs_dir, "test_run_*.txt")), reverse=True)
        if log_files:
            print(f"   No expected items provided, using latest log: {log_files[0]}")
            expected_items = extract_expected_from_log(log_files[0], ollama)
        else:
            print("   ⚠️  No expected items and no log files found")

    # Wait for ORDER COMPLETE screen — the app takes a few minutes to navigate
    # there after the voice agent confirms the order.
    wait_for_order_complete_screen(driver)

    # Detect screen and verify
    screen = detect_screen(driver)
    print(f"\n   🔍 Detected screen: {screen.replace('_', ' ').upper()}")

    if screen == "order_complete":
        results = verify_order_complete(driver, expected_items, ollama)
    else:
        print("   ❌ ORDER COMPLETE screen not detected — cannot verify order details.")
        results = {
            "passed": False,
            "score": 0,
            "matched_items": [],
            "missing_items": expected_items or [],
            "extra_items": [],
            "reasoning": "ORDER COMPLETE screen did not appear within the wait timeout.",
        }

    # Save report
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    report_path = os.path.join(
        logs_dir, f"order_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    print_report(results, log_filepath=report_path)

    return results


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("ORDER VERIFICATION - STANDALONE MODE")
    print("=" * 60)

    expected = None
    log_path = None

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.endswith(".txt"):
            log_path = arg
            print(f"   Using log file: {log_path}")
        else:
            expected = sys.argv[1:]
            print(f"   Using expected items: {expected}")

    driver = AppiumDriver("config/appium_config.yaml")

    try:
        driver.start()
        time.sleep(2)

        results = verify_order(driver, expected_items=expected, log_file=log_path)

        if results.get("passed"):
            print("\n✅ ORDER VERIFICATION PASSED")
            sys.exit(0)
        else:
            print("\n❌ ORDER VERIFICATION FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            driver.stop()
        except Exception:
            pass
