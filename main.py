#!/usr/local/bin/python3

import requests
import json
import smtplib
import re
from email.mime.text import MIMEText
from secrets import email, two_factor_auth
import pandas as pd

NOT_FOUND = "NOT FOUND"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup?id="


def get_id(url):
    result = re.search("id(\w)*", url)
    id_group = result.group()
    # The prefix of the id is "id"
    id = id_group[2:]
    return id


def get_data_from_apple(itunes_id):
    url = ITUNES_LOOKUP_URL + itunes_id
    response = requests.get(url)

    if response.status_code == 200:
        return json.loads(response.text).get('results')[0]
    else:
        raise Exception(
            f"An error occurred with Apple request {response.text}")


def send_email(html):
    subject = "Subject: Daily Price Watch List\n"
    msg = MIMEText(html, 'html').as_string()
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    status, text = smtpObj.starttls()
    status, text = smtpObj.login(email, two_factor_auth)
    # Send email to me
    result = smtpObj.sendmail(
        email, email, subject + msg)
    return


def create_html_email(items_info):
    html = "<html><ul>"
    for item in items_info:
        html = html + (
            f"<li>"
            f"Title: {item.get('title')}<br>"
            f"<b>Price: ${item.get('price')} {item.get('currency')}</b><br>"
            f"URL: <a href=\"{item.get('url')}\">{item.get('url')}</a><br>"
            f"</li>")

    html += "</ul></html>"
    return html


def get_item_urls():
    df = pd.read_csv('itunes_watch_list.csv')
    return df["Watch List"].values.tolist()


def main():
    item_urls = get_item_urls()
    all_items = []

    for interested_item_url in item_urls:
        item_itunes_id = get_id(interested_item_url)
        item_information = get_data_from_apple(item_itunes_id)
        if item_information:
            relevant_item_info = dict(title=item_information.get('collectionName', NOT_FOUND),
                                      price=item_information.get(
                'collectionPrice', NOT_FOUND),
                currency=item_information.get('currency', NOT_FOUND),
                url=item_information.get('collectionViewUrl', NOT_FOUND))
            all_items.append(relevant_item_info)

    html_email_content = create_html_email(all_items)
    send_email(str(html_email_content))


main()
