import os
import time
import uuid
import boto3
import asyncio
import argparse
import meadowrun
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def main_local(query):
    scraper = Scraper(query, False)
    scraper.scrape()


def main_remote(query):
    os.system(
        "wget https://chromedriver.storage.googleapis.com/109.0.5414.74/chromedriver_linux64.zip"
    )
    os.system("unzip chromedriver_linux64.zip")
    os.system("mv chromedriver /usr/bin/chromedriver")
    os.system(
        "wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    )
    os.system("apt install ./google-chrome-stable_current_amd64.deb -y")
    # # install chrome
    # os.system("curl https://intoli.com/install-google-chrome.sh | bash")
    # os.system("mv /usr/bin/google-chrome-stable /usr/bin/google-chrome")
    # os.system("google-chrome --version && which google-chrome")
    scraper = Scraper(query, True)
    scraper.scrape()


class Scraper:
    def __init__(self, query: str = "", remote_deployment: bool = False):
        if query != "":
            self.main_url = f"https://lexica.art/?q={query}"
        else:
            self.main_url = "https://lexica.art/"

        # if remote_deployment:
        options = Options()

        self.browser = webdriver.Chrome(options=options)
        # else:
        # self.browser = webdriver.Chrome()

        self.main_url = self.main_url
        self.prompt_list = []
        self.url_list = []
        self.data_chunk_size = 5
        self.max_images = 100000
        self.current_count = 0
        self.scroll_pause_time = 5
        self.refresh_interval_counter = 1

    def scrape(self):
        self.browser.get(self.main_url)
        while self.current_count < self.max_images:
            # Scroll down twice to load more images
            # Scrape images on current page
            self.loop_through_images()
            # Refresh page
            self.refresh_interval_counter += 1
            # ie not a query
            if "?q=" not in self.main_url:
                print("Refreshing page")
                self.browser.refresh()
                time.sleep(5)
            else:
                print("scrolling down")
                # scroll down to bottom of page as refresh doens't regenerate images
                self.scroll_down()

        # write file to s3 bucket
        s3 = boto3.resource("s3")
        print("Uploading file to s3 bucket")
        try:
            query = self.main_url.split("q")[-1]
        except:
            query = "all"
        s3.meta.client.upload_file(
            "dataset.tsv", "lexica-dataset", f"{str(uuid.uuid4())}-{query}-dataset.tsv"
        )

    def scroll_down(self):
        # Scroll down to bottom
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(self.scroll_pause_time)

    def loop_through_images(self):
        # select all img tags
        img_tags = self.browser.find_elements(By.TAG_NAME, "img")
        # remove images that have already been scraped
        # Iterate over img_tags clicking on each one and copying the image url
        time.sleep(2)
        self.current_count += len(img_tags)
        for img in img_tags:
            try:
                # Scroll to image
                actions = ActionChains(self.browser)
                actions.move_to_element(img).perform()
                time.sleep(1)
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
                    EC.visibility_of_element_located(
                        (By.XPATH, '//div[text()="Copy URL"]')
                    )
                ).click()
                self.url_list = self.write_data_from_clipboard(self.url_list)
                time.sleep(3)
                webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
                print(self.url_list, self.prompt_list)
                time.sleep(3)
            except Exception as e:
                print(e)
                continue
            if len(self.prompt_list) == self.data_chunk_size:
                print("Logging")
                self.append_data_to_file(self.prompt_list, self.url_list)
        print("End of loop Logging remenants")
        self.append_data_to_file(self.prompt_list, self.url_list)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="scary")
    args = parser.parse_args()

    main_local(args.query)
