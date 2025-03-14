import json
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class ProductMatcher:
    def __init__(self, json_file):
        self.json_file = json_file
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def load_amazon_products(self):
        """Load Amazon product details from JSON."""
        with open(self.json_file, 'r', encoding='utf-8') as file:
            return json.load(file)

    def search_ulta_product(self, product_name):
        """Search for a product on Ulta and return its details."""
        self.driver.get("https://www.ulta.com/")
        
        # Handle cookie consent
        try:
            WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
            ).click()
        except:
            pass

        # Search execution
        search_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input#searchInput"))
        )
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)

        # Wait for results
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-listing"))
        )
        self.driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(1)

        # Get product details
        products = self.driver.find_elements(By.CSS_SELECTOR, "div.product-card")[:1]
        
        if not products:
            return None
            
        first_product = products[0]
        return {
            "name": first_product.find_element(By.CSS_SELECTOR, "a.product-card__name").text.strip(),
            "price": first_product.find_element(By.CSS_SELECTOR, "span.prod-card-price").text.strip(),
            "link": first_product.find_element(By.CSS_SELECTOR, "a.product-card__name").get_attribute("href")
        }

    def match_products(self):
        """Match Amazon products with Ulta products."""
        amazon_products = self.load_amazon_products()
        matched_products = []

        for product in amazon_products:
            ulta_product = None
            try:
                ulta_product = self.search_ulta_product(product['name'])
            except:
                pass
            
            matched_products.append({
                "Amazon Name": product['name'],
                "Amazon Price": product['price'],
                "Ulta Name": ulta_product['name'] if ulta_product else "No match found",
                "Ulta Price": ulta_product['price'] if ulta_product else "N/A",
                "Ulta Link": ulta_product['link'] if ulta_product else "N/A"
            })
            time.sleep(1)

        return matched_products

    def save_to_csv(self, matched_products, output_file="matched_products.csv"):
        """Save matched products to CSV."""
        pd.DataFrame(matched_products).to_csv(output_file, index=False)
        print(f"✅ Data saved to {output_file}")

    def close(self):
        """Close the browser."""
        self.driver.quit()

# Run the scraper
if __name__ == "__main__":
    matcher = ProductMatcher("amazon_products.json")
    try:
        matched_data = matcher.match_products()
        matcher.save_to_csv(matched_data)
    finally:
        matcher.close()