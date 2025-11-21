#!/usr/bin/env python3
"""
Script to fetch current cryptocurrency prices and save them to a file.
This script is designed to be run by a GitHub Action daily at 12:00 PM UTC.
"""

import json
import requests
from datetime import datetime

# List of cryptocurrencies to track (symbol: name)
CRYPTO_LIST = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "cardano": "Cardano",
    "solana": "Solana",
    "ripple": "Ripple",
    "dogecoin": "Dogecoin",
    "polkadot": "Polkadot",
    "litecoin": "Litecoin",
    "chainlink": "Chainlink",
    "stellar": "Stellar"
}

def fetch_crypto_prices():
    """Fetch current prices for specified cryptocurrencies from CoinGecko API."""
    prices = {}
    try:
        # Using CoinGecko API to get cryptocurrency prices
        url = "https://api.coingecko.com/api/v3/simple/price"
        
        # Prepare parameters for API request
        ids = ','.join(CRYPTO_LIST.keys())
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24h_change': True,
            'include_market_cap': True,
            'include_24h_vol': True
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        for crypto_id, name in CRYPTO_LIST.items():
            if crypto_id in data:
                crypto_data = data[crypto_id]
                prices[name] = {
                    'symbol': crypto_id.upper(),
                    'price_usd': crypto_data.get('usd'),
                    'price_change_24h': crypto_data.get('usd_24h_change'),
                    'market_cap': crypto_data.get('usd_market_cap'),
                    'volume_24h': crypto_data.get('usd_24h_vol'),
                    'timestamp': datetime.utcnow().isoformat() + "Z"
                }
        
        return prices
    
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def update_readme(prices):
    """Update README file with the latest cryptocurrency prices."""
    if prices is None:
        print("No data to update in README")
        return False

    try:
        # Read current README content
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # Find the start and end markers for crypto prices
        start_marker = "<!-- CRYPTO_PRICES_START -->"
        end_marker = "<!-- CRYPTO_PRICES_END -->"

        start_index = readme_content.find(start_marker)
        end_index = readme_content.find(end_marker)

        if start_index == -1 or end_index == -1:
            print("README markers not found. Please add <!-- CRYPTO_PRICES_START --> and <!-- CRYPTO_PRICES_END --> markers to your README.")
            return False

        # Prepare the new crypto prices table
        prices_table = "\n## Latest Cryptocurrency Prices\n\n"
        prices_table += "| Cryptocurrency | Symbol | Price (USD) | 24h Change | Market Cap |\n"
        prices_table += "|--------------|--------|-------------|------------|------------|\n"

        for name, data in prices.items():
            price = f"${data['price_usd']:,.2f}" if data['price_usd'] else "N/A"
            change = f"{data['price_change_24h']:+.2f}%" if data['price_change_24h'] is not None else "N/A"
            market_cap = f"${data['market_cap']:,.0f}" if data['market_cap'] else "N/A"

            prices_table += f"| {name} | {data['symbol']} | {price} | {change} | {market_cap} |\n"

        prices_table += f"\n*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n"

        # Replace the content between markers
        updated_readme = (
            readme_content[:start_index + len(start_marker)] +
            prices_table +
            readme_content[end_index:]
        )

        # Write the updated README
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_readme)

        print("README.md updated with latest cryptocurrency prices")
        return True

    except Exception as e:
        print(f"Error updating README: {e}")
        return False


def save_crypto_data(prices):
    """Save cryptocurrency data to JSON files."""
    if prices is None:
        print("No data to save")
        return False

    filename = f"crypto_prices_{datetime.utcnow().strftime('%Y%m%d')}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(prices, f, indent=2, ensure_ascii=False)

        # Also update the main file that always has the latest data
        with open('latest_crypto_prices.json', 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.utcnow().isoformat() + "Z",
                'prices': prices
            }, f, indent=2, ensure_ascii=False)

        # Update README with latest prices
        update_readme(prices)

        print(f"Cryptocurrency data saved to {filename} and latest_crypto_prices.json")
        print("README.md updated with latest prices")
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False

def main():
    """Main function to run the script."""
    print("Fetching cryptocurrency prices...")
    prices = fetch_crypto_prices()
    
    if prices:
        success = save_crypto_data(prices)
        if success:
            print("Cryptocurrency prices fetched and saved successfully!")
            return 0
        else:
            print("Failed to save cryptocurrency prices")
            return 1
    else:
        print("Failed to fetch cryptocurrency prices")
        return 1

if __name__ == "__main__":
    exit(main())