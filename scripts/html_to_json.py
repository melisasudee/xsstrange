import json
import os
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='[HTML2JSON] %(message)s')

CASES_DIR = "cases"
INDEX_FILE = "templates/index_cases.json"


def find_html_files():
    html_files = []
    for root, dirs, files in os.walk(CASES_DIR):
        for f in files:
            if f.endswith(".html"):
                html_files.append(os.path.join(root, f))
    return html_files


def parse_case_html(path):
    logging.info(f"Parsing HTML: {path}")

    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    info = soup.find("div", class_="case-info")
    article = soup.find("article")

    if info is None or article is None:
        logging.error(f"Missing case-info or article: {path}")
        return None

    # Extract fields
    title = info.find("h1").text.strip()
    difficulty = info.find("span", class_="difficulty").text.strip()
    category = info.find("span", class_="category").text.strip()
    risk = info.find("span", class_="risk").text.strip()
    description = info.find("div", class_="description").text.strip()

    objectives = [li.text.strip() for li in info.find("div", class_="objectives").find_all("li")]
    hints = [li.text.strip() for li in info.find("div", class_="hints").find_all("li")]

    return {
        "title": title,
        "difficulty": difficulty,
        "category": category,
        "risk": risk,
        "description": description,
        "objectives": objectives,
        "hints": hints,
        "status": "active",
        "type": "html",
        "body": str(article)
    }


def update_index(category, slug):
    logging.info(f"Updating index_cases.json: category={category}, slug={slug}")

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    found = False
    for entry in data:
        if entry["category"] == category:
            found = True
            if "test_cases" not in entry["details"]:
                entry["details"]["test_cases"] = []
            if slug not in entry["details"]["test_cases"]:
                entry["details"]["test_cases"].append(slug)

    if not found:
        logging.error(f"Category {category} not found in index_cases.json")
        return False

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


def process_html(path):
    parsed = parse_case_html(path)
    if parsed is None:
        return False

    slug = os.path.splitext(os.path.basename(path))[0]
    category = parsed["category"]

    json_path = os.path.join(os.path.dirname(path), slug + ".json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    logging.info(f"Created JSON: {json_path}")

    if update_index(category, slug):
        logging.info("Index updated successfully.")
    else:
        logging.error("Index update failed.")

    os.remove(path)
    logging.info(f"Deleted HTML: {path}")

    return True


def main():
    logging.info("HTML → JSON Processor Started")

    html_files = find_html_files()
    if not html_files:
        logging.info("No HTML files found. Nothing to convert.")
        return

    logging.info(f"Found {len(html_files)} HTML case files.")

    count = 0
    for html in html_files:
        if process_html(html):
            count += 1

    logging.info(f"Done! Converted {count}/{len(html_files)} HTML files.")


if __name__ == "__main__":
    main()
