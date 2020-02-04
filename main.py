#!/usr/local/bin/python3

import requests
import json
import smtplib
import re
from email.mime.text import MIMEText
from secrets import email, two_factor_auth
import pandas as pd
from math import isnan

NOT_FOUND = "NOT FOUND"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup?id="
ITUNES_WATCH_LIST_FILENAME = "itunes_watch_list.csv"


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


def main():
    all_items = []

    df = pd.read_csv(ITUNES_WATCH_LIST_FILENAME)
    for i in range(len(df.values)):
        url = df.values[i][0]
        item_itunes_id = get_id(url)
        item_information = get_data_from_apple(item_itunes_id)
        if item_information:
            relevant_item_info = dict(title=item_information.get('collectionName', NOT_FOUND),
                                      price=item_information.get(
                'collectionPrice', NOT_FOUND),
                currency=item_information.get('currency', NOT_FOUND),
                url=item_information.get('collectionViewUrl', NOT_FOUND))
            all_items.append(relevant_item_info)

            new_price = float(relevant_item_info.get('price'))
            old_price = float(df.at[i, 'Latest Price']) if not isnan(
                float(df.at[i, 'Latest Price'])) else None

            if not old_price or new_price < old_price:
                df.at[i, 'Latest Price'] = new_price

    html_email_content = create_html_email(all_items)
    send_email(str(html_email_content))
    df.to_csv(ITUNES_WATCH_LIST_FILENAME, index=False)


main()
