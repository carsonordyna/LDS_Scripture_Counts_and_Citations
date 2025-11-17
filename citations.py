

# Import packages
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re
import requests
import time
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")



# Read in the verse counts dataset ("VerseCounts.csv"). This data set can created by running "counts.py", which
# will take roughly 20-30 minutes to finish
counts_df = pd.read_csv("VerseCounts.csv")

# This is a dictionary mapping URL codes to books. It may be obtained using the code found in "counts.py"
code_to_book_dict = {'gen': 'Genesis', 'ex': 'Exodus', 'lev': 'Leviticus', 'num': 'Numbers', 'deut': 'Deuteronomy',
                     'josh': 'Joshua', 'judg': 'Judges', 'ruth': 'Ruth', '1-sam': '1 Samuel', '2-sam': '2 Samuel',
                     '1-kgs': '1 Kings', '2-kgs': '2 Kings', '1-chr': '1 Chronicles', '2-chr': '2 Chronicles',
                     'ezra': 'Ezra', 'neh': 'Nehemiah', 'esth': 'Esther', 'job': 'Job', 'ps': 'Psalms',
                     'prov': 'Proverbs', 'eccl': 'Ecclesiastes', 'song': 'Song of Solomon', 'isa': 'Isaiah',
                     'jer': 'Jeremiah', 'lam': 'Lamentations', 'ezek': 'Ezekiel', 'dan': 'Daniel', 'hosea': 'Hosea',
                     'joel': 'Joel', 'amos': 'Amos', 'obad': 'Obadiah', 'jonah': 'Jonah', 'micah': 'Micah',
                     'nahum': 'Nahum', 'hab': 'Habakkuk', 'zeph': 'Zephaniah', 'hag': 'Haggai', 'zech': 'Zechariah',
                     'mal': 'Malachi', 'matt': 'Matthew', 'mark': 'Mark', 'luke': 'Luke', 'john': 'John', 'acts': 'Acts',
                     'rom': 'Romans', '1-cor': '1 Corinthians', '2-cor': '2 Corinthians', 'gal': 'Galatians',
                     'eph': 'Ephesians', 'philip': 'Philippians', 'col': 'Colossians', '1-thes': '1 Thessalonians',
                     '2-thes': '2 Thessalonians', '1-tim': '1 Timothy', '2-tim': '2 Timothy', 'titus': 'Titus',
                     'philem': 'Philemon', 'heb': 'Hebrews', 'james': 'James', '1-pet': '1 Peter', '2-pet': '2 Peter',
                     '1-jn': '1 John', '2-jn': '2 John', '3-jn': '3 John', 'jude': 'Jude', 'rev': 'Revelation',
                     '1-ne': '1 Nephi', '2-ne': '2 Nephi', 'jacob': 'Jacob', 'enos': 'Enos', 'jarom': 'Jarom',
                     'omni': 'Omni', 'w-of-m': 'Words of Mormon', 'mosiah': 'Mosiah', 'alma': 'Alma', 'hel': 'Helaman',
                     '3-ne': '3 Nephi', '4-ne': '4 Nephi', 'morm': 'Mormon', 'ether': 'Ether', 'moro': 'Moroni',
                     'dc': 'Doctrine and Covenants', 'moses': 'Moses', 'abr': 'Abraham', 'js-m': 'Joseph Smith—Matthew',
                     'js-h': 'Joseph Smith—History', 'a-of-f': 'Articles of Faith'}

# Initialize list of codes for the standard works
standard_works = ['ot', 'nt', 'bofm', 'dc-testament', 'pgp']


# Extract a list of speaker codes for each conference
base_url = 'https://www.churchofjesuschrist.org/study/general-conference/'

# Keep a running list of citation counts during the General Conferences of the last 10 years
citation_counts = []

for year in range(2016, 2026):
    for month in ['04', '10']:

        # Scrape the webpage
        conference_url = base_url + str(year) + '/' + month
        time.sleep(2)  # Maintain a short delay between requests
        conference_r = requests.get(conference_url, verify=False)
        conference_soup = BeautifulSoup(conference_r.content)
        speakers = [tag['href'] for tag in conference_soup.find_all('a')]

        # Clean list of speakers to extract URL codes
        speakers_codes = []
        for speaker in speakers:
            if (str(year) in speaker) and (('/04/' in speaker) or ('/10/' in speaker)):
                speakers_code = ' '.join(speaker.split('/')[speaker.split('/').index(month)+1:]).split('?')[0]
                if ('session' not in speakers_code) and ('sustaining-of-church-officers' not in speakers_code):
                    if ('auditing-department' not in speakers_code) and ('statistical-report' not in speakers_code):
                        if speakers_code not in speakers_codes:
                            speakers_codes.append(speakers_code)



        # For each talk/speaker, get a list of cited/quoted/referenced verses
        for code in speakers_codes:
            talk_citations = []

            # Scrape the webpage for the speaker/talk
            speaker_url = base_url + str(year) + '/' + month + '/' + code
            time.sleep(2)  # Maintain a short delay between requests
            speaker_r = requests.get(speaker_url, verify=False)
            speaker_href = re.findall(r'scriptures\/[^"]+"', speaker_r.text)

            # # Extract references from the links
            for href in speaker_href:
                work = href.split('scriptures/')[1].split('/')[0]
                if work in standard_works:

                    # Extract book, chapter, and verse(s) from the links of referenced scriptures
                    book_code = href.split('scriptures/')[1].split('/')[1]
                    if book_code in code_to_book_dict:  # Only "valid" references
                        book = code_to_book_dict[book_code]
                        chapter = int(href.split('scriptures/')[1].split('/')[2].split('?')[0])

                        # Check if the reference is to verses or a whole chapter
                        if len(href.split(';id=')) > 1:
                            verse_list = href.split(';id=')[1].split('#')[0].split(',')

                            # Handle cases of multiple verses (e.g. 1 Nephi 4:6-7)
                            for verse_item in verse_list:
                                if '-' in verse_item:

                                    # Make sure the range of verses is valid
                                    if verse_item.split('-')[0][1:].isdigit():
                                        first_verse = int(verse_item.split('-')[0][1:])
                                    elif verse_item.split('-')[0].isdigit():
                                        first_verse = int(verse_item.split('-')[0])
                                    if verse_item.split('-')[1][1:].isdigit():
                                        last_verse = int(verse_item.split('-')[1][1:]) + 1
                                    elif verse_item.split('-')[1].isdigit():
                                        last_verse = int(verse_item.split('-')[1]) + 1

                                    # Add each verse in the range
                                    for verse in range(first_verse, last_verse):
                                        if [book, chapter, verse] not in talk_citations:
                                            talk_citations.append([book, chapter, verse])

                                else:
                                    if verse_item[1:].isdigit():  # Only verses — not chapter introductions
                                        verse = int(verse_item[1:])
                                        if [book, chapter, verse] not in talk_citations:
                                            talk_citations.append([book, chapter, verse])

                        else:
                            verse_count = counts_df[(counts_df['Book'] == book) &
                                                    (counts_df['Chapter'] == chapter)]['Verse_Count'].iloc[0]
                            for i in range(verse_count):
                                talk_citations.append([book, chapter, i+1])
                    
                    # If an entire book is referenced
                    elif book_code.split('?')[0] in code_to_book_dict:
                        book = code_to_book_dict[book_code.split('?')[0]]
                        for i in range(counts_df[counts_df['Book'] == book].shape[0]):
                            chapter = counts_df[counts_df['Book'] == book]['Chapter'].iloc[i]
                            verse_count = counts_df[counts_df['Book'] == book]['Verse_Count'].iloc[i]
                            for j in range(verse_count):
                                talk_citations.append([book, chapter, j+1])

                    # Out of curiosity print, the href's that are not being included (e.g. The Introduction to the Book of Mormon)
                    # else:
                    #     print([href, book_code.split('?')[0]])
                        

            # Append citations from the talk to a running list
            citation_counts.append(talk_citations)


# Convert the "citation_counts" list to a DataFrame
rows = []
for row_list in citation_counts:
    for row in row_list:
        rows.append({
            'Book':row[0],
            'Chapter':row[1],
            'Verse':row[2]
        })
df = pd.DataFrame(rows)

# Calculate citation counts, sort the verses by citation count in descending order, and reset the index
df = df.groupby(['Book', 'Chapter', 'Verse']).size().reset_index(name='Citations')
df.sort_values('Citations', ascending = False, inplace = True)
df.reset_index(drop = True, inplace = True)


# Save the DataFrame as a CSV file
df.to_csv("VerseCitations.csv", index = False)



# Obtain the text of each verse; Only include verses with at least 8 citations (roughly 1,000 verses)
df = df[df['Citations'] >= 8]
verse_text = []
book_to_code_dict = dict(map(reversed, code_to_book_dict.items()))
work_to_code_dict = {'Old Testament':'ot', 'New Testament':'nt', 'Book of Mormon':'bofm',
                     'Doctrine and Covenants':'dc-testament', 'Pearl of Great Price':'pgp'}
for i in range(df.shape[0]):
    work = work_to_code_dict[counts_df[counts_df['Book'] == df['Book'].iloc[i]]['Standard_Work'].iloc[0]]
    book_code = book_to_code_dict[df['Book'].iloc[i]]
    chapter = df['Chapter'].iloc[i]
    verse_number = df['Verse'].iloc[i]

    # Scrape the webpage
    verse_url = f"https://www.churchofjesuschrist.org/study/scriptures/{work}/{book_code}/{chapter}"
    time.sleep(2)  # Maintain a short delay between requests
    verse_r = requests.get(verse_url, verify=False)
    verse_soup = BeautifulSoup(verse_r.content)
    text = verse_soup.find("p", id=f"p{verse_number}")
    text = [tag.get_text() for tag in text]
    text_cleaned = ''
    for segment in text[1:]:
        text_cleaned += segment

    # Append to running list
    verse_text.append(text_cleaned)


# Remove unwanted leading characters from the verses' texts
unwanted = [str(i) for i in range(200)] + ['¶']  # Make a list of unwanted leading characters
new_text = []
for text_i in verse_text:
    if (text_i.split(' ')[0] in unwanted) and (text_i.split(' ')[1] in unwanted):
        new_text.append(' '.join(text_i.split(' ')[2:]).strip())
    elif text_i.split(' ')[0] in unwanted:
        new_text.append(' '.join(text_i.split(' ')[1:]).strip())
    else:
        new_text.append(text_i.strip())

# Assign the list to a column in the DataFrame
df['Text'] = new_text


# Add standard works and chapter verse counts by merging with "counts_df"
df = df.merge(counts_df, on=["Book", "Chapter"])

# Reorder the columns
df['Chapter_Verse_Count'] = df['Verse_Count']
df = df[['Standard_Work', 'Book', 'Chapter', 'Verse', 'Citations', 'Text', 'Chapter_Verse_Count']]



# Save the DataFrame as a CSV file
df.to_csv("Verses.csv", index = False)

