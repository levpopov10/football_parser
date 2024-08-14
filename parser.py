import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from datetime import datetime

# Set up the Selenium WebDriver options
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode, remove this if you want to see the browser

# Initialize the WebDriver
driver = webdriver.Chrome(options=options)

# Read URLs from a text file
with open('links.txt', 'r') as file:
    url_list = [url.strip() for url in file.readlines()]

# Display available URLs and ask the user to select one
print("Available URLs:")
for idx, url in enumerate(url_list, start=1):
    print(f"{idx}. {url}")

# Loop until the user selects a valid URL
selected_url_idx = -1
while selected_url_idx < 0 or selected_url_idx >= len(url_list):
    try:
        selected_url_idx = int(input("Select a URL by number: ")) - 1
        if selected_url_idx < 0 or selected_url_idx >= len(url_list):
            print("Invalid selection. Please enter a valid number.")
    except ValueError:
        print("Invalid input. Please enter a number.")

selected_url = url_list[selected_url_idx]

# Prompt the user to enter the number of matches to parse
num_matches_to_parse = int(input("Enter the number of matches to parse: "))

# Prepare a list to hold all match data
matches_data = []

# Open the selected URL
driver.get(selected_url)

# Wait for the container to load
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'container__liveTableWrapper')))
    time.sleep(5)  # Wait for the page to fully load if necessary
except Exception as e:
    print(f"Error waiting for page to load: {e}")

# Get the page's HTML source after it has loaded
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Find all match elements
match_elements = soup.find_all('div', class_='event__match')

# Parse the selected number of matches
for match_div in match_elements[:num_matches_to_parse]:
    a_tag = match_div.find('a', class_='event__match--withRowLink')
    if a_tag:
        link = a_tag.get('href')
        if link:
            match_url = selected_url + link  # Construct the full URL
            print(f"Processing {match_url}")

            # Open each match URL
            driver.get(match_url)

            # Wait for the page to load
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'container__detail')))
                time.sleep(5)  # Wait for the page to fully load if necessary
            except Exception as e:
                print(f"Error waiting for page to load: {e}")
                continue  # Skip to the next link if there is a problem

            # Get the page's HTML source after it has loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Extract home and away team names
            home_team_div = soup.find('div', class_='duelParticipant__home')
            away_team_div = soup.find('div', class_='duelParticipant__away')

            home_team_name = "N/A"
            away_team_name = "N/A"

            if home_team_div:
                home_name_wrapper = home_team_div.find('div', class_='participant__participantNameWrapper')
                if home_name_wrapper:
                    home_name_tag = home_name_wrapper.find('a', class_='participant__participantName')
                    if home_name_tag:
                        home_team_name = home_name_tag.text.strip()

            if away_team_div:
                away_name_wrapper = away_team_div.find('div', class_='participant__participantNameWrapper')
                if away_name_wrapper:
                    away_name_tag = away_name_wrapper.find('a', class_='participant__participantName')
                    if away_name_tag:
                        away_team_name = away_name_tag.text.strip()

            print(f"{home_team_name} vs {away_team_name}")

            # Find and print the final score
            duel_participant_scores = soup.find_all('div', class_='duelParticipant__score')

            # Collect data from <span> tags for scores
            score_texts = []
            for score_div in duel_participant_scores:
                spans = score_div.find_all('span')
                for span in spans:
                    score_texts.append(span.text.strip())

            # Join all score texts into a single line
            final_score = " - ".join(score_texts)
            print(f"Final Score: {final_score}")

            # Extract match time and date
            time_date_div = soup.find('div', class_='event__time')
            match_time = time_date_div.text.strip() if time_date_div else 'N/A'
            print(f"Match Time: {match_time}")

            # Parse the date and time into a datetime object for proper sorting
            match_datetime = datetime.strptime(match_time, "%d.%m.%Y %H:%M") if match_time != 'N/A' else None

            # Extract additional match statistics
            stats = {
                "Ball Possession": ("N/A", "N/A"),
                "Goal Attempts": ("N/A", "N/A"),
                "Shots on Goal": ("N/A", "N/A"),
                "Corner Kicks": ("N/A", "N/A"),
                "Red Cards": ("N/A", "N/A"),
                "Dangerous Attacks": ("N/A", "N/A")
            }

            # Find the container element for statistics
            element = soup.find('body', class_='soccer flat _fs pid_2 detailbody responsive brand--flashscore')
            if element:
                parent_element = element.find('div', class_='container__detail')
                if parent_element:
                    parent_element2 = parent_element.find('div', class_='container__detailInner')
                    if parent_element2:
                        # Now find the <section> element inside the parent element
                        section_element = parent_element2.find('div', class_='section')
                        if section_element:
                            # Find all divs with class _row_1nw75_8 inside the section
                            divs = section_element.find_all('div', class_='_row_1nw75_8')
                            # Extract data from each div
                            for div in divs:
                                name_div = div.find('div', class_='_category_1ague_4')
                                if name_div:
                                    name = name_div.text
                                    if name in stats:
                                        home_value_div = div.find('div', class_='_value_1jbkc_4 _homeValue_1jbkc_9')
                                        away_value_div = div.find('div', class_='_value_1jbkc_4 _awayValue_1jbkc_13')
                                        home_value = home_value_div.text if home_value_div else "N/A"
                                        away_value = away_value_div.text if away_value_div else "N/A"
                                        stats[name] = (home_value, away_value)

            # Append match data to the list, including new statistics
            matches_data.append({
                "Date and Time": match_datetime,
                "URL": selected_url,
                "Home Team": home_team_name,
                "Away Team": away_team_name,
                "Final Score": final_score,
                "Ball Possession Home": stats["Ball Possession"][0],
                "Ball Possession Away": stats["Ball Possession"][1],
                "Goal Attempts Home": stats["Goal Attempts"][0],
                "Goal Attempts Away": stats["Goal Attempts"][1],
                "Shots on Goal Home": stats["Shots on Goal"][0],
                "Shots on Goal Away": stats["Shots on Goal"][1],
                "Corner Kicks Home": stats["Corner Kicks"][0],
                "Corner Kicks Away": stats["Corner Kicks"][1],
                "Red Cards Home": stats["Red Cards"][0],
                "Red Cards Away": stats["Red Cards"][1],
                "Dangerous Attacks Home": stats["Dangerous Attacks"][0],
                "Dangerous Attacks Away": stats["Dangerous Attacks"][1],
                "Match Link": match_url
            })

# Close the WebDriver
driver.quit()

# Create a DataFrame from the match data
df = pd.DataFrame(matches_data)

# Sort the DataFrame by Date and URL
df.sort_values(by=["Date and Time", "URL"], inplace=True)

# Define the path to save the Excel file on the desktop
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
file_path = os.path.join(desktop_path, "match_results.xlsx")

# Save the DataFrame to an Excel file with multiple sheets
with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='Sorted by Date', index=False)
    df.sort_values(by=["URL", "Date and Time"], inplace=True)
    df.to_excel(writer, sheet_name='Sorted by URL', index=False)

    # Adjust column width for better readability
    for sheet_name in writer.sheets:
        worksheet = writer.sheets[sheet_name]
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col))
            worksheet.set_column(idx, idx, max_length + 2)  # Add extra padding

print(f"Data saved to {file_path}")


