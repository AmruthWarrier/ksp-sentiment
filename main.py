import json
from flask import Flask, request, jsonify
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
from googlesearch import search

app = Flask(__name__)

def analyze_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity == 0:
        return 'neutral'
    else:
        return 'negative'

def retrieve_recent_posts(query, num_posts=5):
    search_results = search(query, num=num_posts)
    posts = []
    for result in search_results:
        parts = result.split(' - ')
        title = parts[0]
        snippet = parts[1] if len(parts) > 1 else ''
        posts.append({
            'title': title,
            'snippet': snippet,
            'sentiment': analyze_sentiment(title + ' ' + snippet)
        })
    return posts

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "hello"}), 200

@app.route('/recent_posts', methods=['GET'])
def get_recent_posts():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    recent_posts = retrieve_recent_posts(query)
    return jsonify(recent_posts)

def scrape_instagram_posts(username):
    url = f"https://www.instagram.com/{username}/"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tags = soup.find_all('script', type="text/javascript")
        for script_tag in script_tags:
            if script_tag.string and script_tag.string.startswith('window._sharedData'):
                shared_data = script_tag.string.split(' = ', 1)[1].rstrip(';')
                data = json.loads(shared_data)
                if 'entry_data' in data and 'ProfilePage' in data['entry_data']:
                    edges = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
                    captions = [edge['node']['edge_media_to_caption']['edges'][0]['node']['text'] for edge in edges if edge['node']['edge_media_to_caption']['edges']]
                    return captions
                else:
                    return None
        return None
    else:
        return None

@app.route('/instagram_posts', methods=['GET'])
def get_instagram_posts():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username parameter is required"}), 400

    captions = scrape_instagram_posts(username)
    if captions:
        return jsonify({"captions": captions}), 200
    else:
        return jsonify({"error": "Failed to retrieve Instagram posts"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)