from facebook_tools import open_facebook, open_target_page, process_followers



driver = open_facebook()

open_target_page(driver, "https://www.facebook.com/rajadaniyalahmadofficial/friends")
process_followers(driver)