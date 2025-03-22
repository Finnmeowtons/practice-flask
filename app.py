from __future__ import print_function
import random
from flask import Flask, render_template, request, jsonify
import sys
import requests
import pycountry
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)

# Spotify API credentials - Replace these with your actual credentials
client_id = '4e95ea97f48145279a7b58fd79a152ec'
client_secret = '175383caa21a442794aa68cd8fd43fa3'

# Initialize Spotify client with credentials
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Home route - Displays the search page
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

# Search route - Handles the place search and fetches data
@app.route("/search", methods=["POST"])
def search():
    place = request.form["place"]
    
    # Get information about the place using Wikipedia API
    wiki_response = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{place}")
    wiki_data = wiki_response.json()

    # Extract relevant information (place name, description, image URL, coordinates)
    place_name = wiki_data["title"]
    place_description = wiki_data["extract"]
    image_url = wiki_data["originalimage"]["source"]
    latitude = None
    longitude = None
    
    # Check if coordinates are available
    if "coordinates" in wiki_data:
        latitude = wiki_data["coordinates"]["lat"]
        longitude = wiki_data["coordinates"]["lon"]

    # Get the country code using the place name
    country_code = get_country_code(place_name)
    
    print(f"country_code:{country_code}", file=sys.stderr)
    
    try:
        # Formulate a query to search for trending songs in the place using Spotify API
        query = f"trending songs in {place_name}"
        offset = random.randint(1, 11)  # Randomly pick a track from the top 10 results
        
        # Perform the Spotify search, considering the country code if available
        if country_code:
            results = sp.search(q=query, type='track', market=country_code, offset=offset, limit=1)
        else:
            results = sp.search(q=query, type='track', offset=offset, limit=1)
        
        print(f"results: {results}", file=sys.stderr)
        trending_tracks = []

        # Extract track ID for embedding into the Spotify player
        print(f"RESULT: {results['tracks']['items'][0]['id']}", file=sys.stderr)
        for item in results['tracks']['items']:
            track_id = item['id']
            trending_tracks.append(track_id)
    
    except Exception as e:
        print(f"Error fetching tracks from Spotify: {e}", file=sys.stderr)
        trending_tracks = []

    print(f"Trending tracks:{trending_tracks}", file=sys.stderr)
    
    # Return JSON response containing place and song data
    return jsonify({
        "place_name": place_name,
        "place_description": place_description,
        "image_url": image_url,
        "latitude": latitude,
        "longitude": longitude,
        "trending_tracks": trending_tracks
    })

# Function to get country code using pycountry
def get_country_code(place_name):
    """
    Gets the 2-letter country code for a given place name.

    Args:
        place_name: The name of the place.

    Returns:
        The 2-letter country code, or None if not found.
    """
    try:
        country = pycountry.countries.search_fuzzy(place_name)[0]
        return country.alpha_2
    except LookupError:
        return None

if __name__ == "__main__":
    app.run(debug=True)
