import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# --- Configuration ---
# Use the URL you provided
BASE_URL = "https://www.myntra.com/personal-care?f=Categories%3ALipstick"
PAGES_TO_SCRAPE = 5  # As requested in the .docx file
OUTPUT_FILE = "myntra_products.csv"

def get_product_data(page_source):
    """Parses the HTML to find product details."""
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find all product containers
    # We look for the 'li' tag with class 'product-base'
    products = soup.find_all('li', class_='product-base')
    
    product_list = []
    for product in products:
        brand = product.find('h3', class_='product-brand')
        name = product.find('h4', class_='product-product')
        price_element = product.find('span', class_='product-discountedPrice')
        
        # Handle cases where some data might be missing
        if brand and name and price_element:
            product_list.append({
                "brand": brand.get_text().strip(),
                "name": name.get_text().strip(),
                "price": price_element.get_text().strip()
            })
    return product_list

def main():
    print("Starting scraper...")
    
    # Set up Selenium to use Chrome
    options = Options()
    options.add_argument('--headless')  # Run without opening a visible browser window
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    all_products = []
    
    for page in range(1, PAGES_TO_SCRAPE + 1):
        # Construct the URL for the current page
        url = f"{BASE_URL}&p={page}"
        print(f"Scraping page {page}: {url}")
        
        driver.get(url)
        
        # Give the dynamic content time to load
        time.sleep(3) 

        # Scroll down to trigger loading of all products
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2) # Wait for products to load after scroll

        # Get the page HTML *after* JavaScript has loaded
        html_content = driver.page_source
        
        # Parse the data
        scraped_data = get_product_data(html_content)
        if not scraped_data:
            print(f"No data found on page {page}. Might be blocked or page structure changed.")
            break
            
        all_products.extend(scraped_data)
        print(f"Found {len(scraped_data)} products on this page.")

    driver.quit()

    # Save the data to a CSV file
    if all_products:
        df = pd.DataFrame(all_products)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nSuccessfully scraped {len(all_products)} products.")
        print(f"Data saved to {OUTPUT_FILE}")
    else:
        print("No products were scraped. CSV file not created.")

if __name__ == "__main__":
    main()