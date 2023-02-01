import os
import time
import boto3
import asyncio
import meadowrun
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main():
    os.system('wget https://chromedriver.storage.googleapis.com/80.0.3987.106/chromedriver_linux64.zip')
    os.system('unzip chromedriver_linux64.zip')
    os.system('mv chromedriver /usr/bin/chromedriver')
    scraper = Scraper()
    scraper.scrape()

class Scraper:
    def __init__(self, main_url: str = "https://lexica.art/"):
        self.main_url = main_url

    def scrape(self):
        self.browser = webdriver.Chrome()
        self.main_url = self.main_url
        self.prompt_list = []
        self.url_list = []
        self.data_chunk_size = 50
        self.max_images = 10000
        self.current_count = 0
        self.scroll_pause_time = 5
        self.historical_images = []
        self.refresh_interval_counter = 1
        # self.browser.get(self.main_url)
        # while self.current_count < self.max_images:
        #     # Scroll down twice to load more images
        #     # Scrape images on current page
        #     self.loop_through_images()
        #     # Refresh page
        #     print('Refreshing page')
        #     self.refresh_interval_counter += 1
        #     self.browser.refresh()
        #     time.sleep(5)

        # write file to s3 bucket
        s3 = boto3.resource("s3")
        print("Uploading file to s3 bucket")
        s3.meta.client.upload_file("dataset.csv", "lexica-dataset", "dataset.csv")

    def scroll_down(self):
        # Scroll down to bottom
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(self.scroll_pause_time)

    def loop_through_images(self):
        # select all img tags
        img_tags = self.browser.find_elements(By.TAG_NAME, "img")
        # remove images that have already been scraped
        img_tags = [img for img in img_tags if img not in self.historical_images]
        # Iterate over img_tags clicking on each one and copying the image url
        time.sleep(2)
        self.current_count += len(img_tags)
        for img in img_tags:
            img.click()
            time.sleep(5)
            if "Lexica Aperture v2" not in self.browser.page_source:
                print("Lexica Aperture v2 not found")
                continue
            # find the element by the text contained in the button
            WebDriverWait(self.browser, 40).until(
                EC.visibility_of_element_located(
                    (By.XPATH, '//div[text()="Copy prompt"]')
                )
            ).click()
            self.prompt_list = self.write_data_from_clipboard(self.prompt_list)
            time.sleep(3)
            WebDriverWait(self.browser, 40).until(
                EC.visibility_of_element_located((By.XPATH, '//div[text()="Copy URL"]'))
            ).click()
            self.url_list = self.write_data_from_clipboard(self.url_list)
            time.sleep(3)
            webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
            print(self.url_list, self.prompt_list)
            time.sleep(3)
            if len(self.prompt_list) == self.data_chunk_size:
                print("Logging")
                self.append_data_to_file(self.prompt_list, self.url_list)
        print("End of loop Logging remenants")
        self.append_data_to_file(self.prompt_list, self.url_list)
        self.historical_images += img_tags

    def append_data_to_file(self, prompt_list, url_list):
        # append data to end of csv file
        with open("./dataset.tsv", "a") as f:
            for prompt, url in zip(prompt_list, url_list):
                f.write(f"\n{prompt}\t{url}")
        self.prompt_list = []
        self.url_list = []

    def write_data_from_clipboard(self, data_list):
        root = tk.Tk()
        root.withdraw()  # to hide the window
        data = root.clipboard_get()
        data_list.append(data)
        return data_list


if __name__ == "__main__":

    asyncio.run(
        meadowrun.run_function(
            main,
            meadowrun.AllocEC2Instance('eu-west-2'),
            meadowrun.Resources(logical_cpu=1, memory_gb=4, max_eviction_rate=80),
        )
    )
