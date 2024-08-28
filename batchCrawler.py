import requests
import json
import logging

logger = logging.getLogger(__name__)

def send_post_request(url):
    endpoint = "http://127.0.0.1:8040/site/crawl"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer hMcAwOvcJ7mpR1Z8GSOdORj20bJp5sPEjFKnbJT5aDs"
    }
    payload = {
        "url": url,
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    return response.status_code, response.text

def batch_requests(sites):
    for url in sites:
        status, response = send_post_request(url)
        logger.info(f"URL: {url}")
        logger.info(f"Status: {status}")
        logger.info(f"Response: {response}")
        logger.info("-" * 50)

# 批量 URL 示例
sites_to_crawl = [
# "https://imageeditor.online"
# "https://history-timeline.net",
# "https://illusiondiffusionweb.com/",
# "https://aiprds.top/",
# "https://ai-cartoon-figure.club/",
# "https://ai-image.tools",
# "https://www.wechatsdk.com/",
# "https://www.undressaitool.com/",
# "https://www.honeychat.ai/",
# "https://www.deepnudeaitool.com/",
# "https://undress-ai.life",
"https://undress-ai.in",
]

batch_requests(sites_to_crawl)