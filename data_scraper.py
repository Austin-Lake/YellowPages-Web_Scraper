import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import filedialog
import csv

def fetch_page(url):
    """Fetches a web page and returns its content."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching page: {response.status_code} {response.reason}")
    return response.content

def extract_job_listings(content):
    """Extracts job listings from a Yellow Pages search page."""
    soup = BeautifulSoup(content, 'html.parser')
    for job_listing in soup.select('.listing__content'):
        name_element = job_listing.select_one('.listing__name')
        name = name_element.text.strip() if name_element else 'Not provided'

        location_element = job_listing.select_one('.listing__address')
        location = location_element.text.strip() if location_element else 'Not provided'
        location_list = location.split()
        location = ' '.join(location_list[:-2]) if len(location_list) > 2 else location

        website_element = job_listing.select_one('.mlr__item--website')
        if website_element:
            website_url = website_element.select_one('a')['href']
            parsed_url = urlparse(website_url)
            query_dict = parse_qs(parsed_url.query)
            website = query_dict.get('redirect', [''])[0] or website_url
        else:
            website = 'Not provided'

        phone_element = job_listing.select_one('.mlr__item--phone')
        phone_list = phone_element.text.strip().split() if phone_element else 'Not provided'
        phone = ' '.join(phone_list[2:])

        yield {'name': name, 'location': location, 'website': website, 'phone': phone}


def get_next_page(soup : BeautifulSoup, base_url):
    next_link = None
    page_span = soup.find('span', {'class': 'pageCount'})
    if page_span:
        current_page, total_pages = page_span.text.strip().split('/')
        current_page = int(current_page.strip())
        total_pages = int(total_pages.strip())
        if current_page < total_pages:
            next_link = f'{base_url}/page-{current_page+1}.html'
    return next_link
        
job_listings = []  # Create a list to hold the job listings

def main(location, occupation, results_file=None):
    global job_listings
    try:
        # Create a new window to display the results
        window = tk.Toplevel(root)
        window.title("Job Listings")

        # Create a scrollbar
        scrollbar = tk.Scrollbar(window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a text widget to display the results
        text_widget = tk.Text(window, width="66", height="33", yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        url = f"https://www.yellowpages.ca/search/si/1/{occupation}/{location}"

        # Create a button to save results to a CSV file
        def save_results():
            filepath = filedialog.asksaveasfilename(defaultextension='.csv')
            if not filepath:
                return
        
            # Write the job listings to the CSV file
            with open(filepath, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file, quoting=csv.QUOTE_NONNUMERIC)
                for job in job_listings:
                    writer.writerow(['Name', job['name']])
                    writer.writerow(['Location', job['location']])
                    writer.writerow(['Website', job['website']])
                    writer.writerow(['Phone Number', job['phone']])
                    writer.writerow('')

        # Create a button to save the job listings to a CSV file
        save_button = tk.Button(window, text="Save to CSV", command=save_results)
        save_button.pack(side='bottom', pady=10)
    

        while True:
            content = fetch_page(url)

            # Check if the CAPTCHA is present on the page
            soup = BeautifulSoup(content, 'html.parser')
            captcha_input = soup.find('input', {'name': 'g-recaptcha-response'})
            if captcha_input:
                raise Exception("CAPTCHA is present, please solve it manually.")

            # Extract the job listings from the page
            for job in extract_job_listings(content):
                name_check = job['name'].split()
                if name_check[0].isdigit():
                    job['name'] = ' '.join(name_check[1:])
                text_widget.insert(tk.END, f"Name: {job['name']}\n")
                text_widget.insert(tk.END, f"Location: {job['location']}\n")
                text_widget.insert(tk.END, f"Website: {job['website']}\n")
                text_widget.insert(tk.END, f"Phone: {job['phone']}\n")
                text_widget.insert(tk.END, f"\n")
                
                if job not in job_listings:
                    job_listings.append(job)

            
            # Check if there are more pages of search results
            next_link = get_next_page(soup, url)
            if not next_link:
                break
            else:
                url = next_link

            # Remove duplicates from the list of job listings
            job_listings = [dict(t) for t in {tuple(d.items()) for d in job_listings}]


    except Exception as e:
        print(str(e))

    # Wait for a short time before making the next request
    time.sleep(1)


def get_input():
    location = location_entry.get()
    job_title = job_title_entry.get()
    main(location, job_title)


root = tk.Tk()
root.title("Job Search")
root.geometry("300x200")

location_label = tk.Label(root, text="Location:")
location_label.pack()

location_entry = tk.Entry(root)
location_entry.pack()

job_title_label = tk.Label(root, text="Occupation:")
job_title_label.pack()

job_title_entry = tk.Entry(root)
job_title_entry.pack()

submit_button = tk.Button(root, text="Submit", command=get_input)
submit_button.pack()

root.mainloop()