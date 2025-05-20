#Consulted these sites https://automatetheboringstuff.com/2e/chapter12/ + https://oxylabs.io/blog/how-to-scrape-google-scholar and this video for the creation of this code https://www.youtube.com/watch?v=XiJWHdnVibY + 
import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import sqlite3
from tabulate import tabulate
import openpyxl

# Step 1: Database setup

database_name = "bibliography.db"
table_name = 'google_scholar_articles'

# Step 2: Initialize database connection and table

def create_db():
    connection = sqlite3.connect(database_name)
    sql = """
        CREATE TABLE IF NOT EXISTS google_scholar_articles (
        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT NOT NULL,
        Author TEXT NOT NULL,
        Abstract TEXT NOT NULL,
        Link TEXT,
        Citation_Count TEXT
    )"""
    connection.execute(sql)
    connection.commit()
    connection.close()

# Step 3: Function to scrape Google Scholar

def scrape_gs(url):
    #the header is created to work around dynamic web pages using Java like Google Scholar
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    #read the URL
    response = requests.get(url, headers=headers)
    
    soup = BeautifulSoup(response.content, "html.parser")
    #connect to db
    connection = sqlite3.connect(database_name)

    #loop through the search page results for the needed elements
    for item in soup.select('[data-lid]'):
        
        titles = item.select('h3')[0].get_text()
        authors = item.select('.gs_a')[0].get_text()
        links = item.select('a')[0]['href']
        abstracts = item.select('.gs_rs')[0].get_text()
        citations_text = item.select('.gs_fl.gs_flb > a:nth-child(3)')
        citations = (citations_text[0].get_text())

        #create data from dictionary of scraped data
        data = {
            'Title': titles,
            'Author': authors,
            'Abstract': abstracts,
            'Link': links,
            'Citation_Count': citations
        }
        
        dataframe = pd.DataFrame([data]) 
        dataframe.to_sql(table_name, connection, if_exists='append', index=False)

    connection.commit()
    connection.close()

    # Query & Display results
    connection = sqlite3.connect(database_name)
    df = pd.read_sql_query("SELECT * FROM google_scholar_articles", connection)
    connection.close()

    table = tabulate(df, headers='keys', tablefmt='pipe')
    print(table)


def main():

    create_db()  
    
    base_url = "https://scholar.google.com/scholar?hl=en&as_sdt=0%2C33&q=fashion+metadata&oq=fas"
    
    #Step 4: Create a loop to scrape more than one page

    for start in range(0,20,10):
        url = f"{base_url}&start={start}"
        print("Scraping Next Page")
        scrape_gs(url)
        time.sleep(2)  # Prevent suspicion from Google Scholar servers

    #Step 5: Export the database to Excel

    connection = sqlite3.connect(database_name)
    
    df = pd.read_sql_query("SELECT * FROM google_scholar_articles", connection)
    df.to_excel("bibliography.xlsx", index=False)
    
    
    #Step 6: Data Cleaning

    #Clean the Author column by removing ellipses

    df['Author'] = df['Author'].str.replace(r'…', '', regex=True).str.strip()

    #Clean the Abstract column to remove the elipses

    df['Abstract'] = df['Abstract'].str.replace(r'…', '', regex=True).str.strip()

    #Ensure the column to split is named 'Header' and split it into four parts

    df[['Author-Journal-Date', 'Online Journal', 'Year']] = df['Author'].str.split(' - ', n=3, expand=True)
   
    #Clean the new Author column 

    df['Author'] = df['Author'].str.replace(',', ' -')

    #Drop the previous author column

    df.drop(columns=['Author'], inplace=True)

    #Drop the year column

    df.drop(columns=['Year'], inplace=True)

    

# Step 7: Save the updated DataFrame back to an Excel file

    df.to_excel("updated_bibliography.xlsx", index=False)

    print("Excel file updated and saved as 'updated_bibliography.xlsx'.")

    connection.close()


# Run the main function
if __name__ == '__main__':
    main()

