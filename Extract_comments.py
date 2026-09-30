import asyncio
import pandas as pd
from playwright.async_api import async_playwright


# Facebook post URL
POST_URL = "https://www.facebook.com/rajadaniyalahmadofficial/posts/pfbid028pWhVhXHK3EmHVz2YaCnhxVDDhiFfmrQoizfJsfs6jhS2LUrdotwvv6y6DKYjeRzl"


# Load the given URL
async def load_page(page, url):
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    return page


# Extract data from the loaded page
async def extract_post_data(page):
    post_elements = page.locator(
        'div[data-ad-preview="message"], div[dir="auto"]'
        # '//div[@data-ad-rendering-role="profile_name"]'
    )

    count = await post_elements.count()
    texts = []

    for i in range(min(count, 20)):
        txt = (await post_elements.nth(i).inner_text()).strip()

        if txt and txt not in texts:
            texts.append(txt)

    return [{"content": t} for t in texts]


# Main scraping function
async def scrape_facebook_post(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )

        page = await context.new_page()

        # First load the page
        await load_page(page, url)

        # Then extract data from the loaded page
        records = await extract_post_data(page)

        await browser.close()

        return records




# Run scraper and save results
async def main():
    records = await scrape_facebook_post(POST_URL)

    df = pd.DataFrame(records)

    print(df)

    df.to_csv("facebook_post_data.csv", index=False)


if __name__ == "__main__":
    asyncio.run(main())
