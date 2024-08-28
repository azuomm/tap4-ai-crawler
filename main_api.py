import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional, List
from datetime import datetime
import sys

# Set up logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f'tap4_ai_crawler_{timestamp}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'),  # Add encoding='utf-8' here
        logging.StreamHandler(stream=sys.stdout)  # Use sys.stdout and specify encoding in the next line
    ],
    encoding='utf-8'  # 添加这一行
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from fastapi import FastAPI, Header, BackgroundTasks, HTTPException
from pydantic import BaseModel

from website_crawler import WebsitCrawler

app = FastAPI()
website_crawler = WebsitCrawler()
load_dotenv()
system_auth_secret = os.getenv('AUTH_SECRET')

logger.debug(f"Loaded AUTH_SECRET: {system_auth_secret}")


class URLRequest(BaseModel):
    url: str
    # tags: Optional[List[str]] = None
    languages: Optional[List[str]] = None


class AsyncURLRequest(URLRequest):
    callback_url: str
    key: str


@app.post('/site/crawl')
async def scrape(request: URLRequest, authorization: Optional[str] = Header(None)):
    logger.info(f"Received scrape request for URL: {request.url}")
    url = request.url
    # tags = request.tags  # tag数组
    languages = request.languages  # 需要翻译的多语言列表

    if system_auth_secret:
        logger.debug("Validating authorization")
        validate_authorization(authorization)

    logger.info(f"Starting website scrape for URL: {url}")
    result = await website_crawler.scrape_website(url.strip(), languages)

    code = 200
    msg = 'success'
    if result is None:
        code = 10001
        msg = 'fail'
        logger.error(f"Scraping failed for URL: {url}")
    else:
        logger.info(f"Scraping successful for URL: {url}")

    response = {
        'code': code,
        'msg': msg,
        'data': result
    }
    logger.debug(f"Returning response: {response}")
    return response


@app.post('/site/crawl_async')
async def scrape_async(background_tasks: BackgroundTasks, request: AsyncURLRequest,
                       authorization: Optional[str] = Header(None)):
    logger.info(f"Received async scrape request for URL: {request.url}")
    url = request.url
    callback_url = request.callback_url
    key = request.key  # 请求回调接口，放header Authorization: 'Bear key'
    # tags = request.tags  # tag数组
    languages = request.languages  # 需要翻译的多语言列表

    if system_auth_secret:
        logger.debug("Validating authorization")
        validate_authorization(authorization)

    logger.info(f"Adding async task for URL: {url}")
    background_tasks.add_task(async_worker, url.strip(),  languages, callback_url, key)

    response = {
        'code': 200,
        'msg': 'success'
    }
    logger.debug(f"Returning response: {response}")
    return response


def validate_authorization(authorization):
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=400, detail="Missing Authorization header")
    if 'Bearer ' + system_auth_secret != authorization:
        logger.warning("Invalid Authorization")
        raise HTTPException(status_code=401, detail="Authorization is error")
    logger.debug("Authorization validated successfully")


async def async_worker(url, languages, callback_url, key):
    logger.info(f"Starting async worker for URL: {url}")
    result = await website_crawler.scrape_website(url.strip(), languages)
    try:
        logger.info(f'Callback begin: {callback_url}')
        response = requests.post(callback_url, json=result, headers={'Authorization': 'Bearer ' + key})
        if response.status_code != 200:
            logger.error(f'Callback error for {callback_url}: {response.text}')
        else:
            logger.info(f'Callback success for {callback_url}')
    except Exception as e:
        logger.exception(f'Callback exception for {callback_url}: {str(e)}')


if __name__ == '__main__':
    import uvicorn

    logger.info("Starting the application")
    uvicorn.run(app, host="127.0.0.1", port=8040)