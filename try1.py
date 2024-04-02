import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import datetime
import hashlib
import csv
import json
import chardet
from textblob import TextBlob
from transformers import pipeline

pipeline_sentiment = pipeline("sentiment-analysis")

def md5sum(article):
    """Calculate MD5 Hash"""
    result = hashlib.md5(article.encode())
    return result.hexdigest()

processed_articles = set()
existing_hashes = set()

def initialize_csv():
    """Initialize the CSV file with column names."""
    fields = ['date', 'hash', 'news_article']
    filename = "daily_market_updates.csv"

    if not os.path.exists(filename):
        with open(filename, mode='w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()

def load_saved_hashes():
    global existing_hashes
    
    if os.path.exists("existing_hashes.txt"):
        with open("existing_hashes.txt", "r") as hashes_file:
            existing_hashes = set(line.strip() for line in hashes_file.readlines())

load_saved_hashes()

def save_new_hashes(new_hashes):
    global existing_hashes

    existing_hashes |= new_hashes
    with open("existing_hashes.txt", "w") as hashes_file:
        for h in existing_hashes:
            hashes_file.write(f"{h}\n")

def process_article(date, headline, news_article):
    combined_article = headline + "\n" + news_article
    article_hash = md5sum(combined_article)

    if article_hash not in existing_hashes:
        processed_articles.add((date, headline, news_article, article_hash))
        existing_hashes.add(article_hash)

def append_to_csv():
    fields = ['date', 'hash', 'news_article']
    filename = "daily_market_updates.csv"

    if os.path.exists(filename):
        with open(filename, mode='a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            for date, headline, news_article, _ in processed_articles:
                writer.writerow({'date': date, 'hash': md5sum(headline+"\n"+news_article), 'news_article': news_article})

initialize_csv()

st.title("Daily Market Updates Scraper & Sentiment Analysis")

todays_date = datetime.datetime.now().strftime("%d/%m/%Y").lower()
col1, col2 = st.columns([2, 1])

with col1:
    url = 'https://boakenya.com/treasury/daily-market-update/'
    response = requests.get(url)
    content = response.text
    soup = BeautifulSoup(content, 'html.parser')

    # Main DIV containing all the info
    main_div = soup.find('div', {'class': 'innerleftcolumn'})

    if main_div:
        market_update_date = todays_date

        raw_date = main_div.p.strong.text
        match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', raw_date.lower())

        if match:
            market_update_date = match.group()

        headline = main_div.h3.text.strip()
        news_article = main_div.find('div', {'class': 'page'}).p.text if main_div.find('div', {'class': 'page'}) else 'No News Article Found.'

        if headline and news_article and (market_update_date != todays_date or md5sum(headline + "\n" + news_article) not in processed_articles):
            process_article(market_update_date, headline, news_article)

            sentiment_results = pipeline_sentiment(news_article)
            sentiment = sentiment_results[0]['label'].capitalize()
            score = sentiment_results[0]['score']

            st.write(f"### **Market Update - {market_update_date}:** *{headline}*")
            st.write(f"Sentiment: {sentiment} ({score})")
            st.write(f"{news_article}")

    else:
        st.warning('No news article found or an error occurred during web scraping. Please try again later.')

append_to_csv()
save_new_hashes(existing_hashes)