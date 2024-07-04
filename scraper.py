import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv

url = 'https://www.prothomalo.com/bangladesh/'
response = requests.get(url)
if response.status_code == 200:
    html_content = response.content
else:
    print(f'Failed to retrieve {url}. Code : {response.status_code}')

soup = BeautifulSoup(html_content, 'html.parser')
child_links = [a['href'] for a in soup.find_all('a', class_='excerpt _4Nuxp')]

news_data = []

for link in child_links:
    child_url = f'https://www.prothomalo.com/bangladesh{link}'
    response = requests.get(child_url)
    child_soup = BeautifulSoup(response.content, 'html.parser')

    content = child_soup.find('div', class_='VzzDZ').get_text()
    news_data.append({'content': content})

with open('articles.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Content'])

    for news in news_data:
        writer.writerow([news['content']])

# Adjust the tag and class based on the website structure
# articles = soup.find_all('div', class_='story-element story-element-text')
# data = []
# for article in articles:
#     summary = article.find('p').text
#     data.append({'summary': summary})

# df = pd.DataFrame(data)
# df.to_csv('news_articles.csv', index=False)
