import sqlite3
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pyperclip


# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect("tracking_params.db")
    cursor = conn.cursor()

    # Create table for tracking rules if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracking_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            param TEXT NOT NULL
        )
    """
    )

    conn.commit()
    conn.close()


# Add a new tracking rule
def add_rule(domain, param):
    conn = sqlite3.connect("tracking_params.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tracking_rules (domain, param) VALUES (?, ?)", (domain, param)
    )
    conn.commit()
    conn.close()


# View all tracking rules
def view_rules():
    conn = sqlite3.connect("tracking_params.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracking_rules ORDER BY domain, param")
    rules = cursor.fetchall()
    conn.close()
    return rules


# Delete a rule by ID
def delete_rule(rule_id):
    conn = sqlite3.connect("tracking_params.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracking_rules WHERE id=?", (rule_id,))
    conn.commit()
    conn.close()


# Get tracking parameters for a specific domain (or global rules)
def get_tracking_params(domain):
    conn = sqlite3.connect("tracking_params.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT param FROM tracking_rules WHERE domain=? OR domain='*'", (domain,)
    )
    params = [row[0] for row in cursor.fetchall()]
    conn.close()
    return params


# Clean the URL by removing tracking parameters
def clean_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    # Fetch tracking parameters for the domain and global rules
    tracking_params = get_tracking_params(domain)

    if "*" in tracking_params:
        # If the wildcard is set for the parameters, remove all query parameters
        cleaned_url = urlunparse(parsed_url._replace(query=""))
        return cleaned_url

    if tracking_params:
        query_params = parse_qs(parsed_url.query)
        clean_params = {
            k: v for k, v in query_params.items() if k not in tracking_params
        }
        new_query = urlencode(clean_params, doseq=True)
        cleaned_url = urlunparse(parsed_url._replace(query=new_query))

        if cleaned_url == url:
            print(f"URL unchanged for: {domain}")
            if query_params:
                print("Query parameters:")
                for param in query_params:
                    print(f"- {param}")
        else:
            print(f"Cleaned URL for: {domain}")
            if query_params:
                print("Removed query parameters:")
                for param in query_params:
                    if param not in clean_params:
                        print(f"- {param}")
                if clean_params:
                    print("Remaining query parameters:")
                    for param in clean_params:
                        print(f"- {param}")

        return cleaned_url

    return url


# Main loop to monitor clipboard and clean URLs
def main():
    last_clipboard = ""
    last_cleaned_content = ""

    while True:
        clipboard_content = pyperclip.paste()

        if (
            clipboard_content != last_clipboard
            and clipboard_content != last_cleaned_content
        ):
            lines = clipboard_content.splitlines()
            cleaned_lines = []

            for line in lines:
                original_line = line
                line = line.strip()
                if line.startswith(("http://", "https://")):
                    cleaned_line = clean_url(line)
                    cleaned_lines.append(cleaned_line)
                    if cleaned_line != line:
                        print(f"Cleaned URL: {cleaned_line}")
                else:
                    cleaned_lines.append(original_line)

            final_content = "\n".join(cleaned_lines)

            if final_content != clipboard_content:
                last_cleaned_content = final_content
                pyperclip.copy(final_content)

        last_clipboard = clipboard_content
        time.sleep(1)


if __name__ == "__main__":
    init_db()

    print("Current tracking rules:")
    for rule in view_rules():
        print(rule)

    main()
