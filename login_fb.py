from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install())
)

driver.get("https://www.facebook.com/")

# Start Chrome
# driver = webdriver.Chrome()

try:
    # Open Facebook
    driver.get("https://www.facebook.com/")

    wait = WebDriverWait(driver, 15)

    # Enter email
    email_field = wait.until(
        EC.visibility_of_element_located((By.XPATH, '//input[@name="email"]'))
    )
    email_field.send_keys("YOUR_EMAIL")

    # Enter password
    password_field = wait.until(
        EC.visibility_of_element_located((By.XPATH, '//input[@name="pass"]'))
    )
    password_field.send_keys("YOUR_PASSWORD")

    # Click Log In
    login_button = wait.until(
        EC.element_to_be_clickable((By.NAME, "login"))
    )
    login_button.click()

    # Keep browser open
    input("Press Enter to close...")

finally:
    driver.quit()