import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import datetime
import json
import csv
import hashlib
import chardet
#import torch
from textblob import TextBlob
from transformers import pipeline

def md5sum(article):
    """Calculate MD5 Hash"""
    result = hashlib.md5(article.encode())
    return result.hexdigest()

processed_items = {}

def initialize_csv():
    """Initialize the CSV file with column names."""
    fields = ['date', 'hash', 'news_article']
    filename = "daily_market_updates.csv"

    if not os.path.exists(filename):
        with open(filename, mode='w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()

def append_to_csv(data):
    """Append data to the CSV file."""
    fields = ['date', 'hash', 'news_article']
    filename = "daily_market_updates.csv"

    if os.path.exists(filename):
        if data not in processed_items.values():
            with open(filename, mode='a', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fields)
                writer.writerow({field: data[field] for field in fields})

            processed_items[len(processed_items)] = data
    else:
        with open(filename, mode='w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fields)
            writer.writeheader()

        append_to_csv(data)

def read_csv():
    """Read the contents of the CSV file."""
    filename = "daily_market_updates.csv"

    if os.path.exists(filename):
        data = []

        with open(filename, mode='r') as csv_file:
            rows = list(csv.DictReader(csv_file, skipinitialspace=True))
            data += rows

        return data
    else:
        return []
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
    sentiment = 'POSITIVE' if sentiment_score > 0 else ('NEGATIVE' if sentiment_score < 0 else 'NEUTRAL')
    return sentiment, abs(sentiment_score)

# def analyze_sentiment(text):
#     blob = textblob(text)
#     sentiment_score = blob.sentiment.polarity
#     sentiment = 'POSITIVE' if sentiment_score > 0 else ('NEGATIVE' if sentiment_score < 0 else 'NEUTRAL')
#     return sentiment, abs(sentiment_score)

def display_news_from_csv(data):
    """Display news from the CSV file along with sentiment analysis results."""
    for idx, d in enumerate(data):
        st.write(f"### **{d['date']}**")
        sentiment, score = analyze_sentiment(d['news_article'])
        st.write(f"Sentiment: {sentiment} ({score})")
        st.write(f"{d['news_article']}")

initialize_csv()
data = read_csv()
display_news_from_csv(data)

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

        combined_article = headline + "\n" + news_article
        article_hash = md5sum(combined_article)

        if article_hash not in processed_items:
            old_data = next((d for d in data if d["hash"] == article_hash), None)

            if not old_data:
                st.write(f"### **Today's News:** *{market_update_date}*")
                st.write(f"{headline}")
                st.write(news_article)

                # Add data to the CSV file
                append_data = {
                    'date': market_update_date,
                    'hash': article_hash,
                    'news_article': news_article
                }
                append_to_csv(append_data)

                st.success(f"Successfully saved article #{len(processed_items)} to the CSV!")
            else:
                print(f"Skipping duplicate entry for {market_update_date}")

            processed_items[article_hash] = {
                'date': market_update_date,
                'hash': article_hash,
                'news_article': news_article
            }
        else:
            print(f"Skipping duplicate entry for {market_update_date}")
    else:
        st.warning('No news article found or an error occurred during web scraping. Please try again later.')