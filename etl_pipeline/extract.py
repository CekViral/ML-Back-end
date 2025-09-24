import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from tqdm import tqdm 
from transform import transform_to_DataFrame, transform_status, clean_description
from upload_gcs import init_storage_client, upload_image_to_gcs
import re


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Referer": "https://turnbackhoax.id/"
}


# Konfigurasi
CHECKPOINT_FILE = "last_checkpoint.txt"
SAVE_EVERY_N_PAGES = 100
OUTPUT_FOLDER = "/Environment/information/data"
BUCKET_NAME = "image_from_scraping"
SERVICE_ACCOUNT_JSON = "/Environment/information/service_account.json"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
storage_client = init_storage_client(SERVICE_ACCOUNT_JSON)


def fetching_content(url, retries=3, delay=5):
    session = requests.Session()
    for attempt in range(retries):
        try:
            response = session.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Percobaan {attempt+1} gagal untuk {url}: {e}")
            time.sleep(delay)
    print(f"Gagal mengambil konten dari {url} setelah {retries} percobaan.")
    return None


def extract_image_url(soup):
    image_tag = soup.find('div', class_='entry-content mh-clearfix').find('img')
    if image_tag and image_tag.get('src'):
        return image_tag['src']
    return None


def extract_news_data(article):
    title_tag = article.find('h3', class_='entry-title mh-loop-title')
    news_title = title_tag.get_text(strip=True) if title_tag else 'No Title'
    link_tag = title_tag.find('a') if title_tag else None
    article_url = link_tag['href'] if link_tag else None

    meta_element = article.find('div', class_='mh-meta mh-loop-meta')
    date_tag = meta_element.find('span', class_='mh-meta-date updated') if meta_element else None
    date = date_tag.get_text(strip=True) if date_tag else 'No Date'

    description = ''
    image_gcs_url = ''

    if article_url:
        detail_content = fetching_content(article_url)
        if detail_content:
            soup_detail = BeautifulSoup(detail_content, "html.parser")
            content_div = soup_detail.find('div', class_='entry-content mh-clearfix')
            if content_div:
                description = content_div.get_text(separator=' ', strip=True)
                image_url = extract_image_url(soup_detail)
                if image_url:
                    try:
                        image_gcs_url = upload_image_to_gcs(storage_client, BUCKET_NAME, image_url)
                    except Exception as e:
                        print(f"Gagal upload gambar: {e}")
            else:
                description = 'No Description Found'
        else:
            description = 'Failed to Fetch Detail'
    else:
        description = 'No Link Found'

    return {
        "Title": news_title,
        "Date": date,
        "Description": description,
        "Link": article_url,
        "ImageURL": image_gcs_url
    }


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return int(f.read().strip())
        except Exception:
            return 1
    return 1


def save_checkpoint(page_number):
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(str(page_number))


def scrape_news(base_url, start_page=1, delay=2, max_pages=10):
    data = []
    page_number = start_page
    pages_scraped = 0
    progress_bar = tqdm(total=max_pages, desc="Scraping Progress", unit="page")

    while pages_scraped < max_pages:
        url = base_url.format(page_number)
        print(f"\nScraping halaman: {url}")
        content = fetching_content(url)
        if not content:
            print("Gagal mengambil halaman, berhenti scraping.")
            break

        soup = BeautifulSoup(content, "html.parser")
        main_content = soup.find('div', id='main-content', class_='mh-loop mh-content')
        articles = main_content.find_all('article') if main_content else []

        if not articles:
            print("Tidak ada artikel ditemukan di halaman ini.")
            break

        for article in articles:
            news = extract_news_data(article)
            data.append(news)

        next_button = soup.find('a', class_='next page-numbers')
        if next_button:
            page_number += 1
            pages_scraped += 1
            progress_bar.update(1)
            time.sleep(delay)
        else:
            print("Tidak ada tombol Next, berhenti scraping.")
            break

        if pages_scraped % SAVE_EVERY_N_PAGES == 0:
            partial_save_path = os.path.join(OUTPUT_FOLDER, f'news_data_partial_page_{page_number}.xlsx')
            df_partial = transform_to_DataFrame(data)
            df_partial = transform_status(df_partial)
            df_partial.to_excel(partial_save_path, index=False)
            print(f"Data sementara disimpan di {partial_save_path}")

        save_checkpoint(page_number)

    progress_bar.close()
    return data


def main():
    BASE_URL = 'https://turnbackhoax.id/page/{}/'
    start_page = load_checkpoint()
    print(f"Mulai scraping dari halaman {start_page}...")
    all_news_data = scrape_news(BASE_URL, start_page=start_page, max_pages=827 - start_page + 1)

    if all_news_data:
        try:
            df_news = transform_to_DataFrame(all_news_data)
            df_news = transform_status(df_news)
            df_news['Description'] = df_news['Description'].apply(clean_description)

            print(df_news)

            final_excel_path = os.path.join(OUTPUT_FOLDER, 'news_data.xlsx')
            df_news.to_excel(final_excel_path, index=False)
            print(f"Data berhasil diekspor ke file Excel final di: {final_excel_path}")

            print("Semua data berhasil disimpan!")
        except Exception as e:
            print(f"Terjadi kesalahan saat proses akhir: {e}")
    else:
        print("Tidak ada data berita yang ditemukan.")

if __name__ == "__main__":
    main()
