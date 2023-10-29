import os
import time
import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from fake_useragent import UserAgent
from waybackpy import WaybackMachineCDXServerAPI
from waybackpy.exceptions import NoCDXRecordFound
import pdfplumber
import re
import json

url = "https://finmasters.com/hedge-fund-letters-to-investors/"
retry_delay = 5  # Time to wait before retrying (in seconds)
max_retries = 1  # Maximum number of retries
CHROME_DRIVER_PATH = "chrome/chromedriver.exe"  # Update this to the path where you placed the Chrome WebDriver
OUTPUT_DIR = "../pdfs/finmaster_all_letters"


def make_request(url, retries=max_retries):
    while retries > 0:
        try:
            response = requests.get(url)
            return response
        except (
            requests.exceptions.RequestException,
            ConnectionError,
            requests.exceptions.SSLError,
        ) as e:
            print(f"Error: {e}")
            retries -= 1
            if retries > 0:
                print(f"Retrying... ({max_retries - retries + 1} of {max_retries})")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Skipping this URL.")
                return None


def setup_selenium_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": os.path.abspath(OUTPUT_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        },
    )
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("acceptInsecureCerts")
    return webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=options)


# def get_new_pdf_links(pdf_links, downloaded_pdfs):
#     # Get the href of each pdf link
#     pdf_links_href = [link["href"] for link in pdf_links]
#     print(f"pdf_links_href count: {pdf_links_href}")

#     # Get the difference between the new pdf links and the already downloaded ones
#     new_pdf_links = list(set(pdf_links_href) - set(downloaded_pdfs))
#     print(f"new_pdf_links count: {len(new_pdf_links)}")

#     # just recording all the new pdf links
#     with open("new_pdf_links.txt", "w") as f:
#         f.write(str(new_pdf_links))

#     return new_pdf_links


# def track_downloaded_pdfs(url):
#     with open("downloaded_pdfs.txt", "r") as f:
#         downloaded_pdfs = list(f.read())

#     downloaded_pdfs.append(url)
#     with open("downloaded_pdfs.txt", "w") as f:
#         f.write(str(downloaded_pdfs))


def wayback(url):
    print("404/403 error, will try wayback machine archive")
    # get a user agent
    ua = UserAgent()
    # user_agent = {'User-Agent':str(ua.chrome)}
    # print(f"we will use this user-agent: {str(ua.chrome)}")
    user_agent = str(ua.chrome)
    cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
    # get the latest snapshot
    try:
        if cdx_api.newest().archive_url:
            print(f"newest url found")
            pdf_url = cdx_api.newest().archive_url
            print(f"Downloading {pdf_url}...")
            try:
                print(f"Driver Downloading {pdf_url}...")
                driver.get(pdf_url)
                print("Downloaded successfully!")
                # track_downloaded_pdfs(pdf_url)
                time.sleep(1)  # Wait for the download to start
            except NoSuchElementException or WebDriverException:
                print(f"Failed to download: {pdf_url}")
                print("Opening the URL in the default web browser...")
                webbrowser.open(pdf_url)
    except NoCDXRecordFound:
        pass


# def cleanup(pdfs):
#     # Remove any PDFs that have (1) or (2) or (3) in their name before .pdf
#     for pdf in pdfs:
#         if pdf.endswith(".pdf"):
#             pdf_name = os.path.join(OUTPUT_DIR, pdf)
#             if pdf_name.find("(") > 0:
#                 os.remove(pdf_name)


def check_url(url):
    print(f"Checking {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 404 or response.status_code == 403:
            wayback(url)
    except ConnectionError:
        print("Connection error")
        pass


# def rename_pdf_with_tickers(pdfs):
#     ticker_pattern = r"\b[A-Z]{2,4}\b(?=\s+\(NASDAQ\)|\s+\(NYSE\))"  # improved regex for stock tickers
#     for pdf in pdfs:
#         if pdf.endswith(".pdf"):
#             pdf_name = os.path.join(OUTPUT_DIR, pdf)
#             with pdfplumber.open(pdf_name) as pdf_file:
#                 text = " ".join(page.extract_text() for page in pdf_file.pages)
#                 tickers = set(re.findall(ticker_pattern, text))
#                 if tickers:
#                     new_name = f"{'_'.join(tickers)}_{pdf}"
#                     os.rename(pdf_name, os.path.join(OUTPUT_DIR, new_name))


# Get all the PDF links from the webpage
response = make_request(url)

# Make sure we got a valid response
# then use beautiful soup to parse the HTML page
# and get all the PDF links as a list
if response is not None and response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    pdf_links = soup.find_all("a", href=lambda href: href and href.endswith(".pdf"))
else:
    print("Failed to fetch the webpage")

# Create a directory to save the PDFs
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set up the Selenium WebDriver before chrome is launched to download other PDFs
driver = setup_selenium_driver()

# if not os.path.exists("downloaded_pdfs.txt"):
#     with open("downloaded_pdfs.txt", "w") as f:
#         f.write("[]")


# with open("downloaded_pdfs.txt", "r") as f:
#     downloaded_pdfs = f.read()
#     # check if we downloaded from this URL before
#     print(f"filtering out already downloaded PDFs...")
#     new_pdf_links = get_new_pdf_links(pdf_links, downloaded_pdfs)
#     print(f"new PDFs to download: {new_pdf_links}")

# Download and save each PDF
# for pdf_url in new_pdf_links:
for link in pdf_links:
    pdf_url = link["href"]
    pdf_name = os.path.join(OUTPUT_DIR, os.path.basename(pdf_url))

    try:
        print(f"Initiating download for: {pdf_url}...")
        check_url(pdf_url)
        print(f"Driver Downloading {pdf_url}...")
        driver.get(pdf_url)
        print("Downloaded successfully!")
        # track_downloaded_pdfs(pdf_url)
        time.sleep(1)  # Wait for the download to start
    except WebDriverException as e:
        if "net::ERR_SSL_VERSION_OR_CIPHER_MISMATCH" in str(e):
            print("SSL error encountered. Skipping...")
            continue  # or handle the error as you see fit
        else:
            raise e  # re-raise the exception if it's a different error
    except NoSuchElementException or WebDriverException:
        print(f"Failed to download: {pdf_url}")
        print("Opening the URL in the default web browser...")
        webbrowser.open(pdf_url)
        continue
driver.quit()

# # Clean up the PDFs
# pdfs = os.listdir(OUTPUT_DIR)
# print(f"before cleanup: {pdfs.count()}")
# cleanup(pdfs)
# print(f"after cleanup: {pdfs.count()}")
