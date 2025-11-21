#!/bin/bash
# Main script to run the daily crypto price fetcher

echo "Starting daily cryptocurrency price fetch process..."

# Check if we're in the correct directory
if [ ! -f "fetch_crypto_prices.py" ]; then
  echo "Error: fetch_crypto_prices.py not found in current directory"
  exit 1
fi

# Run the Python script to fetch crypto prices and update README
python3 fetch_crypto_prices.py

# Check the exit status of the Python script
if [ $? -eq 0 ]; then
  echo "Cryptocurrency prices fetched and README updated successfully!"
  exit 0
else
  echo "Error occurred while fetching cryptocurrency prices"
  exit 1
fi