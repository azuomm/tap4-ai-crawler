from bs4 import BeautifulSoup
import logging
import time
import random
import datetime
from pyppeteer import launch
from util.supabase_util import SupabaseUtil

from util.common_util import CommonUtil
from util.llm_util import LLMUtil
from util.oss_util import OSSUtil

llm = LLMUtil()
oss = OSSUtil()

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

global_agent_headers = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
]

class WebsitCrawler:
    def __init__(self):
        self.browser = None
        self.supabase = SupabaseUtil()

    def extract_social_media_links(self, soup):
        social_media = {
            'facebook': None,
            'linkedin': None,
            'twitter': None,
            'email': None,
            'instagram': None,
            'youtube': None,
        }

        # Find all 'a' tags
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href'].lower()
            if 'facebook.com' in href:
                social_media['facebook'] = href
            elif 'linkedin.com' in href:
                social_media['linkedin'] = href
            elif 'twitter.com' in href or 'x.com' in href:
                social_media['twitter'] = href
            elif 'instagram.com' in href:
                social_media['instagram'] = href
            elif 'youtube.com' in href:
                social_media['youtube'] = href
            elif href.startswith('mailto:'):
                social_media['email'] = href.replace('mailto:', '')

        return social_media

    async def scrape_website(self, url, languages):
        try:
            start_time = int(time.time())
            logger.info(f"开始处理URL: {url}")
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
                logger.info(f"URL已更新为: {url}")

            if self.browser is None:
                logger.info("初始化浏览器")
                self.browser = await launch(headless=True,
                                            ignoreDefaultArgs=["--enable-automation"],
                                            ignoreHTTPSErrors=True,
                                            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                                                  '--disable-software-rasterizer', '--disable-setuid-sandbox'],
                                            handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
                                            executablePath=r'D:\chrome-win\chrome.exe')
                logger.info("浏览器初始化完成")

            logger.info("创建新页面")
            page = await self.browser.newPage()
            user_agent = random.choice(global_agent_headers)
            logger.info(f"设置用户代理: {user_agent}")
            await page.setUserAgent(user_agent)

            logger.info(f"正在访问页面: {url}")
            try:
                await page.goto(url, {'timeout': 60000, 'waitUntil': ['load', 'networkidle2']})
                logger.info("页面加载完成")
            except Exception as e:
                logger.warning(f'页面加载超时,不影响继续执行后续流程:{e}')

            logger.info("获取页面内容")
            origin_content = await page.content()
            soup = BeautifulSoup(origin_content, 'html.parser')

            name = CommonUtil.get_name_by_url(url) or "unknown"
            logger.info(f"给当前网站工具生成唯一的website name以便二级页面跳转: {name}")

            # Ensure name is not empty
            if not name or name.strip() == "":
                name = "unnamed_site_" + str(int(time.time()))
                logger.warning(f"Generated fallback name for URL: {name}")

          
            title = soup.title.string.strip() if soup.title else ''
     

            content = soup.get_text()
            
            logger.info("获取网页description描述")
            description = ''
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description:
                description = meta_description['content'].strip()
            if not description:
                meta_description = soup.find('meta', attrs={'property': 'og:description'})
                if meta_description and meta_description.get('content'):
                    description = meta_description['content'].strip()
            
          
            if not description:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    if len(p.get_text(strip=True)) > 50:  # 确保段落有足够的长度
                        description = p.get_text(strip=True)[:200]  # 限制描述长度为200字符
                        break

            logger.info("-------------获得当前网站的的description结果为：")
            logger.info(description)

            logger.info("翻译description为多语言")
            translated_descriptions = llm.translate_description(description)

            logger.info("使用LLM处理生成的****核心主要内容：")
            new_content = llm.process_detail(content)
            logger.warning(new_content);

            logger.info("准备加tags")
            tags = llm.process_tags(content)
           
            logger.info("===翻译 新内容 为多语言===")
            multi_lang_details = llm.process_languages(new_content)
            
            logger.info("生成和上传截图")
            image_key = oss.get_default_file_key(url)
            screenshot_path = './' + url.replace("https://", "").replace("http://", "").replace("/", "").replace(".", "-") + '.png'
            
            
            await page.setViewport({'width': 1920, 'height': 1080})
            
            
            await page.screenshot({'path': screenshot_path, 'fullPage': False})
            
            
            image_url = oss.upload_file_to_r2(screenshot_path, image_key)
            thumbnail_url = oss.generate_thumbnail_image(url, image_key)

            collection_time = datetime.datetime.now().isoformat()
            website_data = None  # Set to None instead of str(soup)
            star_rating = 0  # 默认值,可能需要从网页中提取或通过其他方式获取
            # category_name = category[0] if category else None  # 使用第一个数组名称作为分类,或者设置为None

            # 暂时取消这个功能
            # logger.info("Extracting social media links")
            # social_media = self.extract_social_media_links(soup)
            # logger.info(f"Extracted social media links: {social_media}")

            result = {
                'name': name,
                'title': title,
                **translated_descriptions,  # Add translated descriptions to the result
                'detail': new_content,
                'tags':tags,
                'url': url,
                'image_url': image_url,
                'thumbnail_url': thumbnail_url,
                'collection_time': collection_time,
                'website_data': website_data,  # This will now be None
                'star_rating': star_rating,
                # 'category_name': category_name,
                **multi_lang_details,  # Add multi-language details to the result
            }

            logger.info("保存数据到Supabase")
            logger.info(result);
            db_result = self.supabase.insert_website_data(result)
            if db_result:
                logger.info(f"数据成功存储到Supabase: {url}")
            else:
                logger.error(f"存储数据到Supabase失败: {url}")

            await page.close()
            logger.info(f"页面处理完成: {url}")
            return result

        except Exception as e:
            logger.error(f"处理{url}站点异常，错误信息: {str(e)}", exc_info=True)
            return None
        finally:
            execution_time = int(time.time()) - start_time
            logger.info(f"处理 {url} 总用时：{execution_time} 秒")