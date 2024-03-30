import requests
import json
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://user:user1@cluster0.prmzp9p.mongodb.net/"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.database01  

def parse_data():
    # shoud consist of: fullname, born_date, born_location, description
    authors = []
    # shoud consist of: tags, author, quote
    qoutes = []
    # list of second parts of addresses of second page
    second_part_links = []
    url = 'http://quotes.toscrape.com'
    html_doc = requests.get(url)
    if html_doc.status_code == 200:
        soup = BeautifulSoup(html_doc.content, 'html.parser')
        all_quote_divs = soup.find_all('div', class_='quote')
        if all_quote_divs:
            for data in all_quote_divs:
                if data:
                    # getting one quote and one author
                    one_quote = data.find('span', class_='text').get_text(strip=True)
                    one_author = data.find('small', class_='author').get_text(strip=True)
                    # getting on list of tags
                    one_tag = data.find('div', class_='tags')
                    all_a_elemets = one_tag.find_all('a', class_='tag')
                    temporary_tags_list = []
                    if all_a_elemets:
                        for a_element in all_a_elemets:
                            temporary_tags_list.append(a_element.text)
                    # adding all data in authors list
                    authors.append(
                        {
                            "tags": temporary_tags_list,
                            "author": one_author,
                            "quote": one_quote
                        }
                    )
            # get second parts of links to author birthday
            some_links = soup.find_all('a', text='(about)')  
            if some_links:      
                for link in some_links:
                    sub_el = str(link).split('"')
                    second_part_links.append(sub_el[1])
    # geting all data from second page
    if second_part_links:
        for second_part_url in second_part_links:
            new_url = url + second_part_url
            html_doc_second_page = requests.get(new_url)
            if html_doc_second_page.status_code == 200:
                # all data fron one page
                soup = BeautifulSoup(html_doc_second_page.content, 'html.parser')
                # getting all data
                author_from_2d_page = soup.find('h3', class_='author-title')
                born_date = soup.find('span', class_='author-born-date')
                born_place = soup.find('span', class_='author-born-location')
                description = soup.find('div', class_='author-description')
                # and adding all data in list quotes
                qoutes.append(
                    {
                        "fullname": author_from_2d_page.text,
                        "born_date": born_date.text,
                        "born_location": born_place.text,
                        "description": description.text.replace('\n', '').lstrip('        ').rstrip("        ")
                    }
                )
    return authors, qoutes

if __name__ == '__main__':
    # getting two lists
    qoutes, authors = parse_data()
    # writing these two lists in two files
    if qoutes:
        with open('quotes.json', 'w', encoding ='utf-8') as f:
            json.dump(qoutes, f, ensure_ascii=False, indent=2)
    if authors:
        with open('authors.json', 'w', encoding ='utf-8') as f:
            json.dump(authors, f, ensure_ascii=False, indent=2)
    try:
        # Loading or Opening authors json file
        with open('authors.json') as file:
            authors_file_data = json.load(file)
        # Loading or Opening quotes json file
        with open('quotes.json') as file:
            quotes_file_data = json.load(file)
    except FileNotFoundError:
        print(f"File is not found by this path {path}")
    try:
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        # adding records to database
        try:
            db.authors.insert_many(authors_file_data)
            db.quotes.insert_many(quotes_file_data)
            print("Successfully added.")
        except Exception as e:
            print("Error during data adding to database:", e)
    except Exception as e:
        print(e)
    