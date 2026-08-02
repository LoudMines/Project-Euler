import cloudscraper
from bs4 import BeautifulSoup
import html

scraper = cloudscraper.create_scraper()

def get_problem_info(number):
    url = f"https://projecteuler.net/problem={number}"
    response = scraper.get(url)
    # Raises an error if one occurred during fetching
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h2")
    if title_tag is None:
        raise ValueError(f"Couldn't find a title for problem {number}.")
    title = title_tag.get_text(strip=True)

    content_div = soup.find("div", class_="problem_content")
    if content_div is None:
        raise ValueError(f"Couldn't find problem content for problem {number}.")

    paragraphs = [
        str(child)
        for child in content_div.contents
        if str(child).strip()
    ]

    description = "".join(paragraphs) if paragraphs else str(content_div)
    description = html.unescape(description)
    description = description.replace("\\", "\\\\")

    return title, description