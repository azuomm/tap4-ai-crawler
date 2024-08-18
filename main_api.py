import asyncio
import logging
import os
import threading
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from website_crawler import WebsitCrawler
import datetime

app = Flask(__name__)
website_crawler = WebsitCrawler()
load_dotenv()
auth_secret = 'Bearer ' + os.getenv('AUTH_SECRET')

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/site/crawl', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')
    tags = data.get('tags', [])
    languages = data.get('languages', [])

    auth_header = request.headers.get('Authorization')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not auth_header:
        return jsonify({'error': 'Authorization is required'}), 400

    if auth_secret != auth_header:
        return jsonify({'error': 'Authorization is error'}), 400

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(website_crawler.scrape_website(url.strip(), tags, languages))

    code = 200
    msg = 'success'
    if result is None:
        code = 10001
        msg = 'fail'
    else:
        # Ensure the result doesn't contain the full website_data
        result.pop('website_data', None)

    response = {
        'code': code,
        'msg': msg,
        'data': result
    }
    return jsonify(response)


@app.route('/site/crawl_async', methods=['POST'])
def scrape_async():
    data = request.get_json()
    url = data.get('url')
    callback_url = data.get('callback_url')
    key = data.get('key')
    tags = data.get('tags', [])
    languages = data.get('languages', [])

    auth_header = request.headers.get('Authorization')

    if not url:
        return jsonify({'error': 'url is required'}), 400

    if not callback_url:
        return jsonify({'error': 'call_back_url is required'}), 400

    if not auth_header:
        return jsonify({'error': 'Authorization is required'}), 400

    if auth_secret != auth_header:
        return jsonify({'error': 'Authorization is error'}), 400

    loop = asyncio.get_event_loop()

    t = threading.Thread(target=async_worker, args=(loop, url, tags, languages, callback_url, key))
    t.start()

    response = {
        'code': 200,
        'msg': 'success'
    }
    return jsonify(response)


def async_worker(loop, url, tags, languages, callback_url, key):
    result = loop.run_until_complete(website_crawler.scrape_website(url.strip(), tags, languages))
    if result:
        result.pop('website_data', None)  # Remove website_data before sending
    try:
        logger.info(f'callback begin:{callback_url}')
        response = requests.post(callback_url, json=result, headers={'Authorization': 'Bearer ' + key})
        if response.status_code != 200:
            logger.error(f'callback error:{callback_url}', response.text)
        else:
            logger.info(f'callback success:{callback_url}')
    except Exception as e:
        logger.error(f'call_back exception:{callback_url}', e)


if __name__ == '__main__':
    asyncio.run(app.run(host='0.0.0.0', port=8040, threaded=False))