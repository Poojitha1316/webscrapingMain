# main.py

from zipRecruiter import Wrapper as ZipRecruiterWrapper
from indeed import IndeedScraper
from career_builder import CareerBuilderScraper
from dice import Wrapper as DiceWrapper

def main():
    # Run ZipRecruiter scraper
    zip_recruiter_wrapper = ZipRecruiterWrapper()
    zip_recruiter_wrapper.run()

    # Run Indeed scraper
    indeed_scraper = IndeedScraper()
    indeed_scraper.run()

    # Run CareerBuilder scraper
    career_builder_scraper = CareerBuilderScraper()
    career_builder_scraper.run()

    # Run Dice scraper
    dice_wrapper = DiceWrapper()
    dice_wrapper.run()

if __name__ == "__main__":
    main()
