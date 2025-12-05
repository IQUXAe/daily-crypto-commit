#!/usr/bin/env python3
"""
Script to fetch current cryptocurrency prices and save them to a file.
This script is designed to be run by a GitHub Action daily at 12:00 PM UTC.
"""

import json
import os
import requests
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, List

# List of cryptocurrencies to track (symbol: name)
CRYPTO_LIST: Dict[str, str] = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "cardano": "Cardano",
    "solana": "Solana",
    "ripple": "Ripple",
    "dogecoin": "Dogecoin",
    "polkadot": "Polkadot",
    "litecoin": "Litecoin",
    "chainlink": "Chainlink",
    "stellar": "Stellar",
    "monero": "Monero",
    "algorand": "Algorand",
    "vechain": "VeChain",
    "ontology": "Ontology",
    "zcash": "Zcash"
}

def fetch_crypto_prices() -> Optional[Dict[str, Any]]:
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
        
        # Added timeout to prevent hanging indefinitely
        response = requests.get(url, params=params, timeout=10)
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
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        return prices
    
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def update_readme(prices: Dict[str, Any], previous_prices: Optional[Dict[str, Any]] = None) -> bool:
    """Update README file with the latest cryptocurrency prices and comparison."""
    if prices is None:
        print("No data to update in README")
        return False

    if previous_prices is None:
        previous_prices = {}

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
        prices_table += "| Cryptocurrency | Symbol | Price (USD) | 24h Change | Price Change (vs Yesterday) | Market Cap |\n"
        prices_table += "|--------------|--------|-------------|------------|---------------------------|------------|\n"

        for name, data in prices.items():
            price = f"${data['price_usd']:,.2f}" if data['price_usd'] else "N/A"
            change = f"{data['price_change_24h']:+.2f}%" if data['price_change_24h'] is not None else "N/A"
            market_cap = f"${data['market_cap']:,.0f}" if data['market_cap'] else "N/A"

            # Calculate change compared to previous day
            prev_change = "N/A"
            if name in previous_prices and data['price_usd'] and previous_prices[name].get('price_usd'):
                prev_price = previous_prices[name]['price_usd']
                current_price = data['price_usd']
                if prev_price != 0:
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    prev_change = f"{change_pct:+.2f}%"

            prices_table += f"| {name} | {data['symbol']} | {price} | {change} | {prev_change} | {market_cap} |\n"

        prices_table += f"\n*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC*\n"

        # Replace the content between markers
        updated_readme_content = (
            readme_content[:start_index + len(start_marker)] +
            prices_table +
            readme_content[end_index:]
        )

        # Write the updated README
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_readme_content)

        print("README.md updated with latest cryptocurrency prices")
        return True

    except Exception as e:
        print(f"Error updating README: {e}")
        return False


def get_previous_data() -> Dict[str, Any]:
    """Get previous day's cryptocurrency data for comparison."""
    try:
        with open('latest_crypto_prices.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('prices', {})
    except FileNotFoundError:
        print("No previous data found, this is the first run")
        return {}
    except Exception as e:
        print(f"Error reading previous data: {e}")
        return {}


def save_crypto_data(prices: Dict[str, Any]) -> bool:
    """Save cryptocurrency data to JSON files."""
    if prices is None:
        print("No data to save")
        return False

    filename = f"crypto_prices_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(prices, f, indent=2, ensure_ascii=False)

        # Also update the main file that always has the latest data
        with open('latest_crypto_prices.json', 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'prices': prices
            }, f, indent=2, ensure_ascii=False)

        # Get previous data for comparison
        previous_prices = get_previous_data()

        # Update README with latest prices and comparison
        update_readme(prices, previous_prices)

        # Generate statistics
        generate_statistics(prices, previous_prices)

        # Check for significant changes
        check_significant_changes(prices, previous_prices)

        # Archive current data
        archive_current_data(prices)

        print(f"Cryptocurrency data saved to {filename} and latest_crypto_prices.json")
        print("README.md updated with latest prices")
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def generate_price_chart(prices: Dict[str, Any]) -> bool:
    """Generate a price chart for the top cryptocurrencies."""
    try:
        # Filter out None values and get top 10 by price
        valid_prices = {name: data for name, data in prices.items() if data['price_usd'] is not None}
        top_crypto = sorted(valid_prices.items(), key=lambda x: x[1]['price_usd'], reverse=True)[:10]

        if not top_crypto:
            print("No valid prices to generate chart")
            return False

        names = [item[0] for item in top_crypto]
        values = [item[1]['price_usd'] for item in top_crypto]

        # Create a horizontal bar chart
        plt.figure(figsize=(10, max(6, len(names) * 0.4)))
        bars = plt.barh(names, values)
        plt.xlabel('Price (USD)')
        plt.title('Top 10 Cryptocurrencies by Price')
        plt.grid(axis='x', linestyle='--', alpha=0.6)

        # Add value labels on bars
        for i, v in enumerate(values):
            plt.text(v, i, f' ${v:,.2f}', va='center', fontsize=9)

        plt.tight_layout()
        plt.savefig('price_chart.png', dpi=150, bbox_inches='tight')
        plt.close()

        print("Price chart generated and saved to price_chart.png")
        return True
    except Exception as e:
        print(f"Error generating price chart: {e}")
        return False


def generate_statistics(prices: Dict[str, Any], previous_prices: Dict[str, Any]) -> bool:
    """Generate and save basic statistics."""
    if not prices:
        print("No prices to generate statistics from")
        return False

    # Generate price chart
    generate_price_chart(prices)

    try:
        # Calculate min/max prices from current data
        all_prices = [data['price_usd'] for data in prices.values() if data['price_usd'] is not None]

        if all_prices:
            min_price = min(all_prices)
            max_price = max(all_prices)

            # Find cryptocurrencies with min/max prices
            min_crypto = next((name for name, data in prices.items() if data['price_usd'] == min_price), None)
            max_crypto = next((name for name, data in prices.items() if data['price_usd'] == max_price), None)

            # Calculate biggest gainers and losers compared to previous day
            biggest_gainer = None
            biggest_loser = None
            max_gain = float('-inf')
            max_loss = float('inf')

            for name, data in prices.items():
                if name in previous_prices and data['price_usd'] and previous_prices[name].get('price_usd'):
                    prev_price = previous_prices[name]['price_usd']
                    current_price = data['price_usd']

                    if prev_price != 0:
                        change_pct = ((current_price - prev_price) / prev_price) * 100

                        if change_pct > max_gain:
                            max_gain = change_pct
                            biggest_gainer = (name, change_pct)
                        if change_pct < max_loss:
                            max_loss = change_pct
                            biggest_loser = (name, change_pct)

            # Create statistics data
            stats = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "min_price": {"crypto": min_crypto, "value": min_price},
                "max_price": {"crypto": max_crypto, "value": max_price},
                "biggest_gainer": biggest_gainer,
                "biggest_loser": biggest_loser,
                "total_cryptos_tracked": len(prices)
            }

            # Save to file
            with open('stats.json', 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            print("Statistics generated and saved to stats.json")
            return True

        return False

    except Exception as e:
        print(f"Error generating statistics: {e}")
        return False


def check_significant_changes(prices: Dict[str, Any], previous_prices: Dict[str, Any]) -> bool:
    """Check for significant price changes and log notifications."""
    try:
        significant_changes = []

        for name, data in prices.items():
            if name in previous_prices and data['price_usd'] and previous_prices[name].get('price_usd'):
                prev_price = previous_prices[name]['price_usd']
                current_price = data['price_usd']

                if prev_price != 0:
                    change_pct = abs(((current_price - prev_price) / prev_price) * 100)

                    # Check if change is greater than 5%
                    if change_pct >= 5.0:
                        direction = "UP" if current_price > prev_price else "DOWN"
                        significant_changes.append({
                            "crypto": name,
                            "change_pct": change_pct,
                            "direction": direction,
                            "previous_price": prev_price,
                            "current_price": current_price
                        })

        if significant_changes:
            # Create notifications file
            notification_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "significant_changes": significant_changes
            }

            with open('notifications.json', 'w', encoding='utf-8') as f:
                json.dump(notification_data, f, indent=2, ensure_ascii=False)

            print(f"Found {len(significant_changes)} significant price changes, logged to notifications.json")

            # Print notifications to console
            for change in significant_changes:
                print(f"🚨 {change['crypto']}: Price changed {change['change_pct']:.2f}% {change['direction']} "
                      f"(${change['previous_price']:.2f} -> ${change['current_price']:.2f})")
        else:
            print("No significant price changes (>5%) detected")

        return True

    except Exception as e:
        print(f"Error checking significant changes: {e}")
        return False


def archive_current_data(prices: Dict[str, Any]) -> bool:
    """Archive current data to an archive directory."""
    try:
        # Create archive directory if it doesn't exist
        archive_dir = "archive"
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)

        # Create filename with current date
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        archive_filename = os.path.join(archive_dir, f"prices_{date_str}.json")

        # Save current prices to archive
        with open(archive_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "date": date_str,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "prices": prices
            }, f, indent=2, ensure_ascii=False)

        # Also keep only last 30 days of archives to avoid unlimited growth
        cleanup_archive(archive_dir)

        print(f"Current data archived to {archive_filename}")
        return True

    except Exception as e:
        print(f"Error archiving data: {e}")
        return False


def cleanup_archive(archive_dir: str, max_days: int = 30) -> bool:
    """Remove archive files older than max_days."""
    try:
        import glob

        # Get all archive files
        archive_files = glob.glob(os.path.join(archive_dir, "prices_*.json"))

        # Sort by date in filename
        archive_files.sort()

        # Keep only the most recent max_days files
        if len(archive_files) > max_days:
            files_to_remove = archive_files[:-max_days]
            for file_path in files_to_remove:
                os.remove(file_path)
                print(f"Removed old archive: {file_path}")

        return True
    except Exception as e:
        print(f"Error cleaning up archive: {e}")
        return False


def main() -> int:
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
