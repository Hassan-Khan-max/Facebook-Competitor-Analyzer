from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
from openpyxl import Workbook, load_workbook


import os
import re
import json
import time
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_URL = "https://www.facebook.com/"

FACEBOOK_USER = os.getenv("FACEBOOK_USER")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")

COOKIE_FOLDER = "facebook_cookies"
EXCEL_FILE = "profiles_data.xlsx"


os.makedirs(COOKIE_FOLDER, exist_ok=True)


def get_cookie_file(user):
    safe_user = re.sub(r"[^a-zA-Z0-9_.-]", "_", user)

    return os.path.join(
        COOKIE_FOLDER,
        f"{safe_user}.json"
    )

def save_cookies(driver, user):
    cookie_file = get_cookie_file(user)

    cookies = driver.get_cookies()

    with open(cookie_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4)

    print(f"Cookies saved: {cookie_file}")

def load_cookies(driver, user):
    cookie_file = get_cookie_file(user)

    if not os.path.exists(cookie_file):
        print("No saved cookies found.")
        return False

    driver.get(FACEBOOK_URL)

    with open(cookie_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    for cookie in cookies:

        # Selenium can sometimes reject these fields
        cookie.pop("sameSite", None)

        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(
                f"Could not add cookie {cookie.get('name')}: {e}"
            )

    driver.refresh()

    time.sleep(2)

    print(f"Cookies loaded for: {user}")

    return True

def is_logged_in(driver):
    time.sleep(1)

    # If login inputs still exist, usually session is not active
    email_fields = driver.find_elements(
        By.XPATH,
        '//input[@name="email"]'
    )

    password_fields = driver.find_elements(
        By.XPATH,
        '//input[@name="pass"]'
    )

    if email_fields and password_fields:
        return False

    return True

def login(driver, user, password):

    wait = WebDriverWait(driver, 15)

    driver.get(FACEBOOK_URL)

    # Enter email / phone
    email_field = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, '//input[@name="email"]')
        )
    )

    email_field.clear()
    email_field.send_keys(user)

    # Enter password
    password_field = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, '//input[@name="pass"]')
        )
    )

    password_field.clear()
    password_field.send_keys(password)

    # Login button
    login_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                '//button[@name="login"] | //*[@aria-label="Log in"]'
            )
        )
    )

    login_button.click()

    time.sleep(120)
    # Give Facebook time to complete login

    # Save cookies after successful login
    if is_logged_in(driver):

        print("Login successful.")

        save_cookies(
            driver,
            user
        )

        return True

    print("Login may require verification / MFA.")

    return False



def open_facebook():
    if not FACEBOOK_USER or not FACEBOOK_PASSWORD:
        raise ValueError(
            "Set FACEBOOK_USER and FACEBOOK_PASSWORD environment variables."
        )


    driver = webdriver.Chrome(
        service=Service(
            ChromeDriverManager().install()
        )
    )

    # try:

    # --------------------------------------------------------
    # Try existing cookies
    # --------------------------------------------------------

    cookies_loaded = load_cookies(
        driver,
        FACEBOOK_USER,

    )

    if cookies_loaded and is_logged_in(driver):

        print(
            f"Already logged in using saved cookies "
            f"for {FACEBOOK_USER}"
        )

    else:

        print(
            f"Cookie session unavailable/expired. "
            f"Logging in as {FACEBOOK_USER}..."
        )

        login(
            driver,
            FACEBOOK_USER,
            FACEBOOK_PASSWORD
        )

    return driver


def open_target_page(driver, profile_url):
    target_url = profile_url

    print(f"Opening target URL in current tab: {target_url}")

    # Open target URL in the current tab
    driver.get(target_url)

    print("Target URL opened in current tab.")

    time.sleep(3)


def press_button(driver, xpath):
    wait = WebDriverWait(driver, 10)

    button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, xpath)
        )
    )

    button.click()

def scroll_modal_to_end(driver, path, pause=3, max_stable_rounds=3, step=1000):

    time.sleep(1)
    wait = WebDriverWait(driver, 15)

    modal = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, path)
        )
    )

    scroll_container = wait.until(lambda d: d.execute_script("""
        const modal = arguments[0];

        function findScrollable(el) {
            if (!el) return null;

            const elements = [el, ...el.querySelectorAll('*')];

            for (const e of elements) {
                const s = getComputedStyle(e);

                if (
                    e.scrollHeight > e.clientHeight &&
                    ['auto', 'scroll', 'overlay'].includes(s.overflowY)
                ) {
                    return e;
                }
            }

            return null;
        }

        return findScrollable(modal);
    """, modal))

    last_height = 0
    stable_rounds = 0

    while stable_rounds < max_stable_rounds:
        driver.execute_script(
            "arguments[0].scrollTop += arguments[1];", scroll_container, step
        )
        time.sleep(pause)

        new_height = driver.execute_script(
            "return arguments[0].scrollHeight;", scroll_container
        )

        if new_height == last_height:
            stable_rounds += 1
        else:
            stable_rounds = 0
            last_height = new_height

    print("Done scrolling. Final height:", last_height)


# def scrape_profile(driver, is_first=False):
#     wait = WebDriverWait(driver, 8)

#     # Profile name load hone tak wait (fixed sleep hata diya)
#     wait.until(lambda d: d.find_elements(By.XPATH, '(//span[@dir="auto"]//div[@role="button"][@tabindex="0"])[1]'))
#     profile_name = driver.find_element(By.XPATH, '(//span[@dir="auto"]//div[@role="button"][@tabindex="0"])[1]').text
#     print("profile name:", profile_name)

#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     time.sleep(1)

#     # Scroll ke baad grid load hone ka dynamic wait
#     try:
#         wait.until(lambda d: d.find_elements(By.XPATH, '//div[@aria-labelledby][@role="list"]'))
#     except:
#         pass

#     items_grid = driver.find_elements(By.XPATH, '//div[@aria-labelledby][@role="list"]')

#     target_titles = ["Personal details", "Details", "Education", "Work"]
#     data = {t: [] for t in target_titles}

#     def collect():
#         for grid in items_grid:
#             try:
#                 title_text = grid.find_element(By.XPATH, './preceding-sibling::div[1]//h2').text.strip()
#             except:
#                 title_text = ""
#             if title_text not in target_titles:
#                 continue
#             items = grid.find_elements(By.XPATH, './/div[@role="listitem"]')
#             for item in items:
#                 data[title_text].append(item.text)

#     collect()

#     # Agar kuch na mila, ek retry (late-loading profiles ke liye)
#     if all(len(v) == 0 for v in data.values()):
#         time.sleep(0.2)
#         items_grid = driver.find_elements(By.XPATH, '//div[@aria-labelledby][@role="list"]')
#         collect()

#     if is_first or not os.path.exists(EXCEL_FILE):
#         wb = Workbook()
#         ws = wb.active
#         ws.append(["Profile Name"] + target_titles)
#     else:
#         wb = load_workbook(EXCEL_FILE)
#         ws = wb.active

#     row = [profile_name] + [", ".join(data[t]) for t in target_titles]
#     ws.append(row)
#     wb.save(EXCEL_FILE)
#     print("Saved:", row)

# def scrape_profile(driver, is_first=False):
#     wait = WebDriverWait(driver, 8)

#     profile_url = driver.current_url

#     # Profile name load hone tak wait (fixed sleep hata diya)
#     wait.until(lambda d: d.find_elements(By.XPATH, '(//span[@dir="auto"]//div[@role="button"][@tabindex="0"])[1]'))
#     profile_name = driver.find_element(By.XPATH, '(//span[@dir="auto"]//div[@role="button"][@tabindex="0"])[1]').text
#     print("profile name:", profile_name)

#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     time.sleep(1)

#     # Scroll ke baad grid load hone ka dynamic wait
#     try:
#         wait.until(lambda d: d.find_elements(By.XPATH, '//div[@aria-labelledby][@role="list"]'))
#     except:
#         pass

#     items_grid = driver.find_elements(By.XPATH, '//div[@aria-labelledby][@role="list"]')

#     target_titles = ["Personal details", "Details", "Education", "Work"]
#     data = {t: [] for t in target_titles}

#     def collect():
#         for grid in items_grid:
#             try:
#                 title_text = grid.find_element(By.XPATH, './preceding-sibling::div[1]//h2').text.strip()
#             except:
#                 title_text = ""
#             if title_text not in target_titles:
#                 continue
#             items = grid.find_elements(By.XPATH, './/div[@role="listitem"]')
#             for item in items:
#                 data[title_text].append(item.text)

#     collect()

#     # Agar kuch na mila, ek retry (late-loading profiles ke liye)
#     if all(len(v) == 0 for v in data.values()):
#         time.sleep(0.2)
#         items_grid = driver.find_elements(By.XPATH, '//div[@aria-labelledby][@role="list"]')
#         collect()

#     if is_first or not os.path.exists(EXCEL_FILE):
#         wb = Workbook()
#         ws = wb.active
#         ws.append(["Profile Name", "Profile URL"] + target_titles)
#     else:
#         wb = load_workbook(EXCEL_FILE)
#         ws = wb.active

#     row = [profile_name, profile_url] + [", ".join(data[t]) for t in target_titles]
#     ws.append(row)
#     wb.save(EXCEL_FILE)
#     print("Saved:", row)



# def process_followers(driver, container_xpath=""):
#     wait = WebDriverWait(driver, 15)
#     main_window = driver.current_window_handle

#     while True:
#         links = driver.find_elements(
#             By.XPATH,
#             f'{container_xpath}//a[@role="link"][@aria-hidden="true"][not(@data-processed="true")]'
#         )

#         if not links:
#             print("No more followers to process. Done.")
#             break

#         link = links[0]

#         driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
#         time.sleep(0.2)

#         href = link.get_attribute("href")

#         driver.execute_script("arguments[0].setAttribute('data-processed', 'true');", link)

#         if not href:
#             continue

#         driver.execute_script("window.open(arguments[0], '_blank');", href)

#         all_windows = driver.window_handles
#         new_window = [w for w in all_windows if w != main_window][0]
#         driver.switch_to.window(new_window)

#         # Page completely load hone ka wait (max 10 sec, fail hone par bhi aage badhega)
#         try:
#             WebDriverWait(driver, 10).until(
#                 lambda d: d.execute_script("return document.readyState") == "complete"
#             )
#             scrape_profile(driver)   # fixed sleep(0.5) hata diya, scrape_profile khud wait karega
#         except:
#             print("Page load timeout, moving on anyway.")


#         try:
#             driver.close()
#         except:
#             pass

#         try:
#             driver.switch_to.window(main_window)
#         except:
#             print("Main window/session lost, stopping.")
#             break


# ==== cluade working =====
# import os, time, json
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from openpyxl import Workbook, load_workbook

# CHECKPOINT_FILE = "checkpoint.json"
# BATCH_SIZE = 200
# TARGET_TITLES = ["Personal details", "Details", "Education", "Work"]
# HEADERS = ["Profile Name", "Profile URL"] + TARGET_TITLES


# # ---------- helpers ----------
# def load_checkpoint():
#     if os.path.exists(CHECKPOINT_FILE):
#         with open(CHECKPOINT_FILE, encoding="utf-8") as f:
#             return json.load(f)
#     return {"last_href": None, "count": 0}


# def flush_buffer(buffer, last_href, total):
#     if not buffer:
#         return True
#     try:
#         if os.path.exists(EXCEL_FILE):
#             wb = load_workbook(EXCEL_FILE); ws = wb.active
#         else:
#             wb = Workbook(); ws = wb.active; ws.append(HEADERS)
#         for r in buffer:
#             ws.append(r)
#         wb.save(EXCEL_FILE)
#     except Exception as e:
#         print("Excel save failed, checkpoint NOT updated:", e)
#         return False
#     with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
#         json.dump({"last_href": last_href, "count": total}, f)
#     buffer.clear()
#     return True


# def skip_to_last(driver, container_xpath, last_href):
#     unproc = f'{container_xpath}//a[@role="link"][@aria-hidden="true"][not(@data-processed="true")]'
#     allx = f'{container_xpath}//a[@role="link"][@aria-hidden="true"]'
#     stale = 0
#     while stale < 8:
#         links = driver.find_elements(By.XPATH, unproc)
#         if not links:
#             stale += 1
#             all_links = driver.find_elements(By.XPATH, allx)
#             if all_links:
#                 driver.execute_script("arguments[0].scrollIntoView({block:'end'});", all_links[-1])
#             time.sleep(1.5)
#             continue
#         stale = 0
#         for l in links:
#             href = l.get_attribute("href")
#             driver.execute_script("arguments[0].setAttribute('data-processed','true');", l)
#             if href == last_href:
#                 print("Last profile mil gayi, aage se scrape hoga.")
#                 return True
#         driver.execute_script("arguments[0].scrollIntoView({block:'end'});", links[-1])
#         time.sleep(1.5)
#     print("Last profile nahi mili!")
#     return False


# # ---------- def 1 ----------
# def scrape_profile(driver):
#     wait = WebDriverWait(driver, 8)
#     profile_url = driver.current_url

#     name_xp = '(//span[@dir="auto"]//div[@role="button"][@tabindex="0"])[1]'
#     wait.until(lambda d: d.find_elements(By.XPATH, name_xp))
#     profile_name = driver.find_element(By.XPATH, name_xp).text

#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     time.sleep(1)

#     grid_xp = '//div[@aria-labelledby][@role="list"]'
#     try:
#         wait.until(lambda d: d.find_elements(By.XPATH, grid_xp))
#     except:
#         pass

#     data = {t: [] for t in TARGET_TITLES}

#     def collect():
#         for grid in driver.find_elements(By.XPATH, grid_xp):
#             try:
#                 title = grid.find_element(By.XPATH, './preceding-sibling::div[1]//h2').text.strip()
#             except:
#                 title = ""
#             if title not in TARGET_TITLES:
#                 continue
#             for item in grid.find_elements(By.XPATH, './/div[@role="listitem"]'):
#                 data[title].append(item.text)

#     collect()
#     if all(len(v) == 0 for v in data.values()):
#         time.sleep(0.2)
#         collect()

#     print("Scraped:", profile_name)
#     return [profile_name, profile_url] + [", ".join(data[t]) for t in TARGET_TITLES]


# # ---------- def 2 ----------
# def process_followers(driver, container_xpath=""):
#     main_window = driver.current_window_handle
#     cp = load_checkpoint()
#     total, last_href = cp["count"], cp["last_href"]
#     buffer, batch_done = [], 0

#     if last_href and not skip_to_last(driver, container_xpath, last_href):
#         return

#     try:
#         while batch_done < BATCH_SIZE:
#             links = driver.find_elements(
#                 By.XPATH,
#                 f'{container_xpath}//a[@role="link"][@aria-hidden="true"][not(@data-processed="true")]'
#             )
#             if not links:
#                 print("No more followers. Done.")
#                 break

#             link = links[0]
#             driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
#             time.sleep(0.2)
#             href = link.get_attribute("href")
#             driver.execute_script("arguments[0].setAttribute('data-processed','true');", link)
#             if not href:
#                 continue

#             driver.execute_script("window.open(arguments[0], '_blank');", href)
#             new_window = [w for w in driver.window_handles if w != main_window][0]
#             driver.switch_to.window(new_window)

#             try:
#                 WebDriverWait(driver, 10).until(
#                     lambda d: d.execute_script("return document.readyState") == "complete")
#                 buffer.append(scrape_profile(driver))
#                 last_href = href
#                 total += 1
#                 batch_done += 1
#             except:
#                 print("Page load timeout, moving on anyway.")

#             try: driver.close()
#             except: pass
#             try: driver.switch_to.window(main_window)
#             except:
#                 print("Session lost, stopping.")
#                 break
#     finally:
#         flush_buffer(buffer, last_href, total)
#         print(f"Total scraped: {total}. Ab restart karo aur manually login karo.")


# # ---------- main ----------
# if __name__ == "__main__":
#     driver = webdriver.Chrome()
#     driver.get("https://...")   # login page
#     input("Login karo, followers list open karo, phir Enter dabao...")
#     process_followers(driver, container_xpath)
#     driver.quit()



import os, time, csv, random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = os.path.dirname(os.path.abspath(__file__))
LINKS_FILE = os.path.join(BASE, "links.txt")
DONE_FLAG  = os.path.join(BASE, "links.done")
CSV_FILE   = os.path.join(BASE, "profiles.csv")
CP_FILE    = os.path.join(BASE, "checkpoint.txt")

BATCH_SIZE = 2000                # itne profiles ke baad return (driver aap khud quit karo)
TITLES = ["Personal details", "Details", "Education", "Work"]
DELAY = (0.3, 0.8)

NAME_XP = '(//span[@dir="auto"]//div[@role="button"][@tabindex="0"])[1]'
GRID_XP = '//div[@aria-labelledby][@role="list"]'

JS = """
const T = arguments[0], out = {};
T.forEach(t => out[t] = []);
document.querySelectorAll('div[aria-labelledby][role="list"]').forEach(g => {
  const p = g.previousElementSibling, h = p && p.querySelector('h2');
  const t = h ? h.innerText.trim() : "";
  if (!T.includes(t)) return;
  g.querySelectorAll('div[role="listitem"]').forEach(i => out[t].push(i.innerText));
});
return out;
"""


def make_driver():
    o = webdriver.ChromeOptions()
    o.page_load_strategy = "eager"
    o.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    return webdriver.Chrome(options=o)


def collect_links(driver, container_xpath=""):
    seen = set(open(LINKS_FILE, encoding="utf-8").read().split()) if os.path.exists(LINKS_FILE) else set()
    xp = f'{container_xpath}//a[@role="link"][@aria-hidden="true"]'
    stale = 0
    prev_last = None
    with open(LINKS_FILE, "a", encoding="utf-8") as f:
        while stale < 120:
            try:
                els = driver.find_elements(By.XPATH, xp)
            except Exception as e:
                if any(k in str(e).lower() for k in ("invalid session", "disconnected", "no such window")):
                    print("Browser closed. Links saved:", len(seen), "- dobara run karo.")
                    return False
                raise
            new = 0
            for e in els:
                try:
                    h = e.get_attribute("href")
                except:
                    continue
                if h and h not in seen:
                    seen.add(h); f.write(h + "\n"); new += 1
            f.flush()
            try:
                last_h = els[-1].get_attribute("href") if els else None
            except:
                last_h = None
            progress = new > 0 or (last_h and last_h != prev_last)
            prev_last = last_h
            stale = 0 if progress else stale + 1

            driver.execute_script("""
                const r = document.evaluate(arguments[0], document, null,
                          XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const n = r.snapshotLength;
                for (let i = 0; i < n - 5; i++) {
                    const a = r.snapshotItem(i);
                    (a.closest('div[role="listitem"]') || a.parentElement).remove();
                }
                if (n) r.snapshotItem(n - 1).scrollIntoView({block: 'end'});
            """, xp)
            if new and len(seen) % 500 < new:
                print("Links:", len(seen))
            time.sleep(1)
    open(DONE_FLAG, "w").write("1")
    print("Total links:", len(seen))


def scrape_profile(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 8)
    wait.until(lambda d: d.find_elements(By.XPATH, NAME_XP))
    name = driver.find_element(By.XPATH, NAME_XP).text
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    # try:
    #     WebDriverWait(driver, 2).until(lambda d: d.find_elements(By.XPATH, GRID_XP))
    # except:
    #     pass
    data = driver.execute_script(JS, TITLES)
    # if not any(data.values()):
    #     time.sleep(0.3)
    #     data = driver.execute_script(JS, TITLES)
    return [name, url] + [", ".join(data[t]) for t in TITLES]


def scrape_all(driver):
    links = open(LINKS_FILE, encoding="utf-8").read().split()
    idx = int(open(CP_FILE).read()) if os.path.exists(CP_FILE) else 0
    new_file = not os.path.exists(CSV_FILE)
    done = 0
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["Profile Name", "Profile URL"] + TITLES)
        while idx < len(links) and done < BATCH_SIZE:
            try:
                w.writerow(scrape_profile(driver, links[idx]))
                f.flush()
                print(idx + 1, "/", len(links))
            except Exception as e:
                msg = str(e).lower()
                if "invalid session" in msg or "disconnected" in msg or "no such window" in msg:
                    print("Session lost, stopping.")
                    break
                print("Skip:", links[idx], type(e).__name__)
            idx += 1
            done += 1
            with open(CP_FILE, "w") as c:
                c.write(str(idx))
            time.sleep(random.uniform(*DELAY))
    print(f"Batch complete. Next index: {idx} / {len(links)}")


def process_followers(driver, container_xpath=""):
    if not os.path.exists(DONE_FLAG):
        collect_links(driver, container_xpath)   # pehli run: followers list open honi chahiye
    scrape_all(driver)