import re
import os
import time
import json
import random
import warnings
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from config import Config
from datetime import datetime, timedelta

# Suppress warnings
warnings.filterwarnings('ignore')

class CareerBuilderScraper:
    def __init__(self):
        # Randomly select a user-agent
        self.user_agent = random.choice(Config.USER_AGENT_LIST)
        self.headers = {'User-Agent': self.user_agent}
        self.proxy = Config.proxy
        self.proxies = {"http": self.proxy, "https": self.proxy}

    # Function to categorize work type based on title
    def categorize_work_type(self, title):
        if 'Onsite' in title:
            return 'On-site'
        elif 'Hybrid' in title:
            return 'Hybrid'
        elif 'Remote' in title:
            return 'Remote'
        else:
            return None

    # Function to convert relative dates to actual dates
    def convert_relative_dates(self, relative_date):
        try:
            if 'today' in relative_date or 'Today' in relative_date:
                return datetime.now().date()
            elif 'yesterday' in relative_date or '1 day ago' in relative_date:
                return (datetime.now() - timedelta(days=1)).date()
            elif 'days ago' in relative_date:
                days_ago = int(relative_date.split()[0])
                return (datetime.now() - timedelta(days=days_ago)).date()
            else:
                return None
        except Exception as e:
            return None

    # Function to get data from the soup object
    def get_data(self, soup):
        try:
            # Extracting job listings using different classes
            job_listings = soup.find_all('div', class_='collapsed-activated')
            all_dataframes = []

            for listing in job_listings:
                listing_soup = BeautifulSoup(str(listing), 'html.parser')
                inner_listings = listing_soup.find_all('li', class_='data-results-content-parent relative bg-shadow')

                inner_dataframes = []

                for inner_listing in inner_listings:
                    job_data = {}
                    inner_soup = BeautifulSoup(str(inner_listing), 'html.parser')

                    try:
                        # Extracting data from the inner listing
                        job_data['publish_time'] = inner_soup.find('div', class_='data-results-publish-time').text.strip()
                        job_data['title'] = inner_soup.find('div', class_='data-results-title').text.strip()
                        job_data['company'] = inner_soup.find('div', class_='data-details').find('span').text.strip()
                        job_data['location'] = inner_soup.find('div', class_='data-details').find_all('span')[1].text.strip()
                        job_data['employment_type'] = inner_soup.find('div', class_='data-details').find_all('span')[2].text.strip()
                        job_url = inner_listing.find('a', class_='data-results-content')['href']
                        job_data['url'] = f"https://www.careerbuilder.com{job_url}"
                        result = inner_soup.select('div.block:not(.show-mobile)')
                        job_data['result'] = result[0].get_text(strip=True)

                        inner_dataframes.append(pd.DataFrame([job_data]))

                    except Exception as e:
                        continue

                try:
                    combined_dataframe = pd.concat(inner_dataframes, ignore_index=True)
                    all_dataframes.append(combined_dataframe)
                except Exception as e:
                    continue

            final_dataframe = pd.concat(all_dataframes, ignore_index=True)
            final_dataframe['Work Location'] = final_dataframe['location'].apply(self.categorize_work_type)
            final_dataframe['Date Posted'] = final_dataframe['publish_time'].apply(self.convert_relative_dates)
            final_dataframe['Current Date'] = datetime.now().date()

            # Column mapping
            columns_mapping = {
                'title': 'Title',
                'company': 'Company',
                'location': 'Location',
                'employment_type': 'Job_type',
                'url': 'Job_url',
                'result': 'Salary'
            }

            final_dataframe.rename(columns=columns_mapping, inplace=True)

            # Extract job IDs and create a new column
            final_dataframe['Job_id'] = final_dataframe['Job_url'].str.extract(r'/job/(.*)')
            final_dataframe.drop(columns=['publish_time'], inplace=True)

            return final_dataframe

        except Exception as e:
            return None

    # Function to run the CareerBuilder scraper
    def run(self):
        # Define the output file path based on the config
        output_directory = Config.output_directory
        output_subdirectory = Config.subdirectory
        output_filename = Config.output_csv_career
        output_path = os.path.join(output_directory, output_subdirectory)
        output_file_path = os.path.join(output_path, output_filename)

        # Initialize lists to store data and soup objects
        dataframes = []
        soups = []

        # Create a session to reuse the same connection
        session = requests.Session()

        try:
            for keyword in Config.keywords:
                keyword_lower = keyword.lower()

                for u in range(0, 20):
                    url = Config.url_career.format(keyword=keyword_lower.replace(" ", "%20"), page=u)

                    try:
                        response = session.get(url, headers=self.headers, proxies=self.proxies, verify=False)
                        response.raise_for_status()

                        if response.status_code == 200:
                            print('Success!')
                        else:
                            print('Sorry, your connection is blocked by the website')
                            continue

                        soup = BeautifulSoup(response.content, 'html.parser')
                        soups.append(soup)
                        result_df = self.get_data(soup)

                        if result_df is None or result_df.empty:
                            print('Sorry, but the bot did not find proper data on this page')
                            continue

                        dataframes.append(result_df)
                        print(f'Success for the page: {u}')

                    except requests.RequestException as e:
                        print(f'Request error for page {u}: {e}')

                    except Exception as e:
                        print(f'Error for page {u}: {e}')

                    time.sleep(5)

        except Exception as e:
            print(f'An unexpected error occurred: {e}')

        # Concatenate dataframes
        final_dataframe = pd.concat(dataframes, ignore_index=True)
        final_dataframe.drop_duplicates(inplace=True)

        # Save the data to the specified file path
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        final_dataframe.to_csv(output_file_path, index=False)

if __name__ == "__main__":
    career_builder_scraper = CareerBuilderScraper()
    career_builder_scraper.run()
