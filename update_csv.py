import pandas as pd
import re

INPUT_FILE = "myntra_products.csv"
OUTPUT_FILE = "myntra_products.csv" # We will overwrite the old file

def generate_dummy_url(brand, name):
    """Generates a simple, clean dummy URL from brand and name."""
    # Convert to lowercase
    brand_slug = brand.lower()
    name_slug = name.lower()
    
    # Remove special characters and replace spaces with hyphens
    brand_slug = re.sub(r'[^a-z0-9\s-]', '', brand_slug).strip().replace(' ', '-')
    name_slug = re.sub(r'[^a-z0-9\s-]', '', name_slug).strip().replace(' ', '-')
    
    # Remove multiple hyphens
    brand_slug = re.sub(r'--+', '-', brand_slug)
    name_slug = re.sub(r'--+', '-', name_slug)
    
    return f"https://www.myntra.com/{brand_slug}-{name_slug}"

print(f"Reading {INPUT_FILE}...")

try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"Error: {INPUT_FILE} not found!")
    exit()
except Exception as e:
    print(f"Error reading file: {e}")
    exit()

# Check if columns already exist
if 'product_url' in df.columns or 'breadcrumbs' in df.columns:
    print("Columns 'product_url' or 'breadcrumbs' already exist. No changes made.")
else:
    print("Adding new columns...")
    
    # 1. Add the static breadcrumbs column
    df['breadcrumbs'] = 'Home/Personal Care/Lipstick'
    
    # 2. Add the dynamic product_url column
    # We apply the function to each row (axis=1)
    df['product_url'] = df.apply(
        lambda row: generate_dummy_url(row['brand'], row['name']),
        axis=1
    )
    
    # 3. Save the file, overwriting the old one
    try:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Successfully updated {OUTPUT_FILE} with new columns!")
    except Exception as e:
        print(f"Error writing to file: {e}")