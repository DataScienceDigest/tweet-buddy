from flask import Flask, render_template, request, jsonify,Response
from twikit import Client
import asyncio
import nest_asyncio
import requests
from flask import send_file
import os
import tempfile
from datetime import datetime
import yt_dlp
import requests
from bs4 import BeautifulSoup
# flexcnic
# Bonegggg
# Fix nested event loop issue in Flask
nest_asyncio.apply()

app = Flask(__name__)

# Setup the Twikit client
client = Client('en-US')
client.load_cookies(r'androess31-cookies.json')

# Global event loop and iterator
loop = asyncio.get_event_loop()
tweet_iter = None

def extract_media_urls(media_data):
    image_urls = []
    video_urls = []

    try:
        for media in media_data:
            # Extract image URLs
            if media.get('type') == 'photo':
                image_urls.append(media.get('media_url_https'))

            # Extract video URLs
            elif media.get('type') == 'video':
                video_variants = media.get('video_info', {}).get('variants', [])
                
                # Filter only video/mp4 and sort by bitrate in descending order
                mp4_variants = [
                    (variant.get('bitrate', 0), variant.get('url'))
                    for variant in video_variants if variant.get('content_type') == 'video/mp4'
                ]
                
                # Sort and get the highest bitrate URL
                if mp4_variants:
                    mp4_variants.sort(reverse=True, key=lambda x: x[0])
                    video_urls.append(mp4_variants[0][1])  # Append URL of the highest bitrate variant
        # print(f"Media: {media}")
        # print(f"Video Variants: {mp4_variants}")
        # print(f"Selected Video URL: {mp4_variants[0][1] if mp4_variants else None}")

    except Exception as e:
        print(f"Error extracting media URLs: {e}")

    return image_urls, video_urls


async def fetch_tweets(query, mode='Top'):
    tweet_objects = []
    try:
        # Fetch initial tweets
        global tweet_iter
        tweet_iter = await client.get_user_by_screen_name(query)
        tweet_iter = await tweet_iter.get_tweets('Tweets')
        # Process each tweet
        for i in tweet_iter:
            media_data = i.media
            # print(i.media,'_______________&&&&&&&&&')
            image_urls, video_urls = [], []  # Default to empty lists
            if media_data is not None:
                image_urls, video_urls = extract_media_urls(media_data)
            tweet_object = {
                'tweets': i.text,
                'image_urls': image_urls if image_urls else None,
                'video_urls': video_urls if video_urls else None
            }

            tweet_objects.append(tweet_object)
        return tweet_objects

    except Exception as e:
        # Handle any exceptions
        error_message = str(e)
        print(f"Error fetching tweets: {error_message}")
        # Return the error message to the frontend
        return jsonify({'error': error_message}), 401

    

async def fetch_next_tweets():
    """Fetch more tweets."""
    global tweet_iter
    tweet_objects = []
    try:
        if tweet_iter:
            more_tweets = await tweet_iter.next()
            tweet_iter = more_tweets
            for i in more_tweets:
                media_data = i.media
                image_urls, video_urls = [], []  # Default to empty lists
                if media_data is not None:
                    image_urls, video_urls = extract_media_urls(media_data)

                # Create a dictionary for the tweet with its associated media
                tweet_object = {
                    'tweets': i.text,
                    'image_urls': image_urls if image_urls else None,
                    'video_urls': video_urls if video_urls else None
                }
                # print(tweet_object,'-=-))))))------------')
                tweet_objects.append(tweet_object)

            # return [tweet.text for tweet in more_tweets]
    except Exception as e:
        # Handle any exceptions
        print(f"Error fetching tweets: {e}")

    return tweet_objects

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """Handle initial tweet search."""
    query = request.form.get('query')
    # tweets = loop.run_until_complete(fetch_tweets(query))
    tweets_data = loop.run_until_complete(fetch_tweets(query))

    return jsonify(tweets=tweets_data)
    # return jsonify(tweets=tweets,image_urls=image_urls,video_urls=video_urls)


@app.route('/next', methods=['GET'])
def next():
    """Fetch next batch of tweets."""
    tweets = loop.run_until_complete(fetch_next_tweets())
    return jsonify(tweets=tweets)


@app.route('/download_media', methods=['GET'])
def download_media():
    media_url = request.args.get('media_url')
    if not media_url:
        return "Media URL is required!", 400
    try:
        response = requests.get(media_url, stream=True, timeout=(10, 300))
        if response.status_code != 200:
            return f"Failed to fetch media: {response.status_code}", response.status_code

        # Extract the file extension
        file_extension = os.path.splitext(media_url)[-1].lower()
        filename = media_url.split('/')[-1]
        if file_extension not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.mov', '.avi']:
            filename += '.mp4'

        # Use a temporary file to store the media
        # print(datetime.now().strftime("%H:%M:%S"),'____________+++++++++++++______________')
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=4 * 1024 * 1024):  # 1 MB
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        # print('after-------------',datetime.now().strftime("%H:%M:%S"),'____________+++++++++++++______________')
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=response.headers.get('Content-Type', 'application/octet-stream')
        )
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
# ---------------get downloadable video link ------------------

@app.route('/get_downloadable_link', methods=['GET'])
def get_downloadable_link():
    video_url = request.args.get('video_url')
    print(video_url)
    if not video_url:
        return jsonify({'success': False, 'error': 'Video URL is required!'}), 400

    try:
        # Logic to fetch the direct video URL
        print(video_url)
        ydl_opts = {
            'format': 'best',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(video_url, download=False)
                if 'entries' in info_dict:
                    downloadable_link_url = info_dict['entries'][0].get('url', None)
                else:
                    downloadable_link_url = info_dict.get('url', None)
            except Exception as e:
                return jsonify({'success': False, 'error': f'Error extracting video info: {e}'}), 500

        if downloadable_link_url:
            return jsonify({'success': True, 'downloadable_link': downloadable_link_url})
        else:
            return jsonify({'success': False, 'error': 'Could not retrieve downloadable link!'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# video downloader section
@app.route('/videos', methods=['GET','POST'])
def videos():
    """Fetch next batch of tweets."""
    if request.method == 'POST':
        video_url = request.form.get('site_url')
        print(video_url,'===+++======')
        
        # Send a GET request to the website
        response = requests.get(video_url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content of the webpage
            soup = BeautifulSoup(response.text, 'html.parser')
            
            li_tags = soup.find_all('li', class_='video')
        
            # Extract data into a list of dictionaries
            video_links = []
            for li in li_tags:
                link = li.find('a', class_='thumb')['href']
                title = li.find('a', class_='title').text.strip()
                thumbnail = li.find('img')['src']
                duration = li.find('div', class_='time').text.strip()
                views = li.find('div', class_='view').text.strip()
                
                video_links.append({
                    'link': link,
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'views': views
                })
        else:
            print(response.status_code ,'++++++++++',response)

            
        return render_template('videos.html',video_links=video_links,video_url=video_url)
    return render_template('videos.html')
    

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True,threaded=True)
    # test
