import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from django.conf import settings
import time
import requests
from bs4 import BeautifulSoup
import re
from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

def search_view(request):
    if request.method == 'POST':
        location = request.POST.get('location')
        num_listings = int(request.POST.get('num_listings')) 
        data = scrape_data(location, num_listings)  
        request.session['data'] = data  
        return render(request, 'result.html', {'businesses': data, 'location': location})
    return render(request, 'search.html')


def scrape_data(location, num_listings):
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
  
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get('https://www.google.com/maps')
    time.sleep(10)  

    search_box = driver.find_element(By.ID, 'searchboxinput')
    search_box.send_keys(location)
    search_box.send_keys(Keys.ENTER)
    time.sleep(15)  

    data = []
    count = 0

    while count < num_listings:
        businesses = driver.find_elements(By.CLASS_NAME, 'Nv2PK')

        for business in businesses:
            if count >= num_listings:  
                break
            try:
                name = business.find_element(By.CLASS_NAME, 'qBF1Pd').text
                address = business.find_element(By.XPATH, ".//div[@class='W4Efsd']/div[@class='W4Efsd'][1]").text  # Address
                phone = 'Phone not available'
                phone_elements = business.find_elements(By.CLASS_NAME, 'UsdlK')
                if phone_elements:
                    phone = phone_elements[0].text
                website = 'Website not available'
                website_buttons = business.find_elements(By.CLASS_NAME, 'lcr4fd')
                if website_buttons:
                    website = website_buttons[-1].get_attribute('href')
                
                email, linkedin, facebook, instagram = extract_social_media(website)

                if email != 'Email not available':
                    data.append({
                        'name': name,
                        'address': address,
                        'phone': phone,
                        'website': website,
                        'email': email,
                        'linkedin': linkedin,
                        'facebook': facebook,
                        'instagram': instagram
                    })

                count += 1

            except Exception as e:
                print(f"Error: {e}")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  

    driver.quit() 
    return data 


def extract_social_media(website):
    email = 'Email not available'
    linkedin = 'LinkedIn not available'
    facebook = 'Facebook not available'
    instagram = 'Instagram not available'
    
    if website != 'Website not available':
        try:
            response = requests.get(website)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', response.text)
            if email_match:
                email = email_match.group(0)

            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'linkedin.com' in href:
                    linkedin = href
                elif 'facebook.com' in href:
                    facebook = href
                elif 'instagram.com' in href:
                    instagram = href

        except Exception as e:
            print(f"Error fetching website: {e}")
    
    return email, linkedin, facebook, instagram


def download_excel(request):
    data = request.session.get('data', [])
    df = pd.DataFrame(data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'google_maps_businesses_{timestamp}.xlsx'

    # Create the excel file as response
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{output_file}"'
    
    df.to_excel(response, index=False)
    return response
