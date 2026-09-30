from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import os
import re
import json
import time
from dotenv import load_dotenv

load_dotenv()



# ============================================================
# Configuration
# ============================================================

FACEBOOK_URL = "https://www.facebook.com/"


FACEBOOK_USER = os.getenv("FACEBOOK_USER")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")

COOKIE_FOLDER = "facebook_cookies"

os.makedirs(COOKIE_FOLDER, exist_ok=True)


# ============================================================
# Create safe cookie filename from email / phone / username
# ============================================================

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

def get_cookie_file(user):
    safe_user = re.sub(r"[^a-zA-Z0-9_.-]", "_", user)

    return os.path.join(
        COOKIE_FOLDER,
        f"{safe_user}.json"
    )


# ============================================================
# Save cookies
# ============================================================

def save_cookies(driver, user):
    cookie_file = get_cookie_file(user)

    cookies = driver.get_cookies()

    with open(cookie_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4)

    print(f"Cookies saved: {cookie_file}")


# ============================================================
# Load cookies
# ============================================================

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

    time.sleep(5)

    print(f"Cookies loaded for: {user}")

    return True


# ============================================================
# Check whether login session appears valid
# ============================================================

def is_logged_in(driver):
    time.sleep(3)

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


# ============================================================
# Login
# ============================================================

def login(driver, user, password, url):

    wait = WebDriverWait(driver, 15)

    driver.get(url)

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

    time.sleep(3)
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




# ============================================================
# Main
# ============================================================
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
        FACEBOOK_USER
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
            FACEBOOK_PASSWORD,
            FACEBOOK_URL
        )

    return driver


def open_target_page(profile_url):
    target_url = profile_url

    # print(f"Opening target URL: {target_url}")

    # driver.get(target_url)
    print(f"Opening target URL in new tab: {target_url}")

    # Open a new tab in the same browser
    driver.execute_script("window.open('about:blank', '_blank');")

    # Switch Selenium to the new tab
    driver.switch_to.window(driver.window_handles[-1])

    # Open target URL in the new tab
    driver.get(target_url)

    print("Target URL opened in new tab.")

    time.sleep(3)

# --------------------------------------------------------
# Your automation starts here
# --------------------------------------------------------

    
    # time.sleep(5)
driver = open_facebook()

open_target_page("https://www.facebook.com/RanaSanaUllahOfficial")
# OPENING A COMMENTS


no_new_posts_retries = 0
max_retries = 3

wait = WebDriverWait(driver, 20)

post_number = 0

while True:

    # Only scroll if there's nothing left to process right now
    unprocessed_buttons = driver.find_elements(
        By.CSS_SELECTOR,
        'div[aria-label="Leave a comment"]:not([data-processed="true"])'
    )

    if not unprocessed_buttons:
        driver.execute_script("window.scrollBy(0, 1000);")  # smaller scroll step
        time.sleep(3)

        unprocessed_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            'div[aria-label="Leave a comment"]:not([data-processed="true"])'
        )

        if not unprocessed_buttons:
            no_new_posts_retries += 1
            print(f"No new unprocessed posts found (attempt {no_new_posts_retries}/{max_retries}).")
            if no_new_posts_retries >= max_retries:
                print("Reached end of feed. Stopping.")
                break
            continue
        else:
            no_new_posts_retries = 0
    else:
        no_new_posts_retries = 0

    comment_button = unprocessed_buttons[0]
    post_number += 1

    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            comment_button
        )
        time.sleep(1)

        try:
            comment_button.click()
        except Exception:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver).move_to_element(comment_button).pause(0.3).click().perform()

        driver.execute_script("arguments[0].setAttribute('data-processed', 'true');", comment_button)

        print(f"Comment section opened for post #{post_number}.")

        time.sleep(3)
        # =====  Go to the reaction part  ======

        press_button(driver, '//div[@role="dialog"]//div[starts-with(@aria-label, "Like:")]')
        time.sleep(3)
        # scroll_modal_to_end(driver, '(//div[@aria-modal="true"][@role="dialog"])[last()]', 2)

        # ===== Click next tabs ======
        tab = driver.find_element(By.XPATH, '(//div[@aria-orientation="horizontal"][@role="tablist"])[last()]//div[@role="tab"][1]')

        # for tab in tabs:
        tab.click()
        # time.sleep(1)
        scroll_modal_to_end(driver, '(//div[@aria-modal="true"][@role="dialog"])[last()]', 1)

        # ===== Click next tabs end ======
        press_button(driver, '(//div[@role="dialog"])[last()]//div[@aria-label="Close"]')


        #=====   Reaction part end here   =====

        scroll_modal_to_end(driver, '//div[@aria-modal="true"]', 1.5, 3, 1200)

        try:
            press_button(driver, '//div[@aria-label="Close"]')
            print(f"Closed and returned to main feed after post #{post_number}.")
        except Exception as e:
            print(f"Could not find/click Close button for post #{post_number}: {e}")

        time.sleep(2)

    except Exception as e:
        print(f"Could not process post #{post_number}: {e}")
        try:
            driver.execute_script("arguments[0].setAttribute('data-processed', 'true');", comment_button)
        except Exception:
            pass
        continue

print(f"\nDone processing all comment buttons. Total processed: {post_number}")




time.sleep(20)
    



# finally:
#     driver.quit()