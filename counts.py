
# Import packages

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import time
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")



# Scrape the webpage
base_url = 'https://www.churchofjesuschrist.org/study/scriptures/'
r = requests.get(base_url, verify=False)
soup = BeautifulSoup(r.content)

# Obtain url codes for each standard work
standard_works = [tag.get_text() for tag in soup.find_all('a', class_='portrait-jkaM1')][:5]
standard_works_codes = [tag['href'].split('?')[0].split('/')[-1] for tag in soup.find_all('a', class_='portrait-jkaM1')][:5]

# For each standard work, obtain the url codes for each book wihin it
work_book_dict = {}
work_book_chapters_dict = {}
all_books = []
all_books_codes = []
for code in standard_works_codes:

    # Scrape the webpage for the given standard work
    url_code = base_url + code
    time.sleep(2)  # Maintain a short delay between requests
    r_code = requests.get(url_code, verify=False)
    soup_code = BeautifulSoup(r_code.content)

    # Obtain a list of all the books
    books = [tag.get_text().replace("\xa0", " ") for tag in soup_code.find_all('p', class_='title')]
    chapters = [tag.get_text().replace("\xa0", " ") for tag in soup_code.find_all('p', class_='title')]
    # Clean "books" list
    books_cleaned = []
    # Specify indices for each list of books for each standard work
    if code == 'ot':
        index = [2, len(books)]
    elif code == 'nt':
        index = [1, len(books)]
    elif code == 'bofm':
        index = [9, -2]
    elif code == 'dc-testament':
        index = [6, -4]   
    elif code == 'pgp':
        index = [2, len(books)]
    else:
        print("Error: Standard Work code not valid")
    for book in books[index[0]:index[1]]:
        if book != "Contents":
            if len(book.split(' ')) == 1:
                if (book not in books_cleaned) and (book != "Facsimiles"):
                    books_cleaned.append(book)
            elif book.split(' ')[-1].isdigit():
                if ' '.join(book.split(' ')[:-1]) not in books_cleaned:
                    if ' '.join(book.split(' ')[:-1]) not in ['Psalm', 'Facsimile']:
                        books_cleaned.append(' '.join(book.split(' ')[:-1]))
    books = books_cleaned
    all_books += books

    # Obtain the url codes for each book
    books_codes = [tag['href'] for tag in soup_code.find_all('a', class_='sc-omeqik-0 ewktus list-tile listTile-WHLxI')]
    books_codes_cleaned = []
    for link in books_codes:
        link_list = link.split('/')
        for j in range(len(link_list)):
            if link_list[j] == code:
                if link_list[j+1] not in books_codes_cleaned:
                    books_codes_cleaned.append(link_list[j+1])
    if code == 'bofm':
        books_codes = books_codes_cleaned[index[0]-1:index[1]]
    elif code == 'dc-testament':
        books_codes = ['dc']
    else:
        books_codes = books_codes_cleaned[index[0]:index[1]]

    all_books_codes += books_codes
    work_book_dict[code] = books_codes
    book_to_code_dict = dict(zip(books, books_codes))

    # Get chapter counts for each book
    chapter_counts = []
    book_chapters_dict = {}
    for book in books:
        if book == 'Psalms':
            book = 'Psalm'
        book_chapters = []
        for chapter in chapters:
            if book in chapter:
                book_chapters.append(chapter)
        if book == 'Psalm':
            book = 'Psalms'
        if book == 'Mormon':
            book_chapters_dict[book_to_code_dict[book]] = 9
        elif book == 'John':
            book_chapters_dict[book_to_code_dict[book]] = 21
        else:
            book_chapters_dict[book_to_code_dict[book]] = int(book_chapters[-1].split(' ')[-1])
    work_book_chapters_dict[code] = book_chapters_dict



# For each chapter in each book of each standard work, obtain the total number of verses
work_book_chapters_verse_dict = {}
for work in work_book_chapters_dict:
    b_c_v_dict = {}
    for book in work_book_dict[work]:
        c_v_dict = {}
        for chapter in [i+1 for i in range(work_book_chapters_dict[work][book])]:

            # Scrape the webpage for each chapter
            url_chapter = base_url + work + '/' + book + '/' + str(chapter)
            time.sleep(2)  # Maintain a short delay between requests
            r_chapter = requests.get(url_chapter, verify=False)
            soup_chapter = BeautifulSoup(r_chapter.content)

            # Obtain the verse count
            verses = int([tag.get_text() for tag in soup_chapter.find_all('span', class_='verse-number')][-1])
            
            # Append to dictionary
            c_v_dict[chapter] = verses
        b_c_v_dict[book] = c_v_dict
    work_book_chapters_verse_dict[work] = b_c_v_dict


# Convert the "work_book_chapters_verse_dict" dictionary to a DataFrame
rows = []
for work, book_dict in work_book_chapters_verse_dict.items():
    for book, chapter_dict in book_dict.items():
        for chapter, verse_count in chapter_dict.items():
            rows.append({
                'Standard_Work': work,
                'Book': book,
                'Chapter': chapter,
                'Verse_Count': verse_count
            })
df = pd.DataFrame(rows)

# Map codes to actual names
df['Standard_Work'] = df['Standard_Work'].map(dict(zip(standard_works_codes, standard_works)))
df['Book'] = df['Book'].map(dict(zip(all_books_codes, all_books)))

# Save the DataFrame as a CSV file
df.to_csv("VerseCounts.csv", index = False)

