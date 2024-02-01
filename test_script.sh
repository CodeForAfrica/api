#!/bin/bash

# Define the URL
url="https://6206-105-163-1-107.ngrok-free.app/root"

# Define the JSON object data
data='{"key1": "value1", "key2": "value2"}'

# Make the POST request using curl
response=$(curl -X POST -H "Content-Type: application/json" -d "$data" "$url")

# Display the response
echo "Response: $response"
