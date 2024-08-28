import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()

class SupabaseUtil:
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL")
        self.key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(self.url, self.key)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def insert_website_data(self, data):
        try:
            # 基本字段列表
            base_fields = ['name', 'title', 'url', 'image_url', 'thumbnail_url', 'collection_time', 
                           'website_data', 'star_rating', 'category_name', 'detail', 'content']
            
            # 支持的语言列表
            languages = ['en', 'jp', 'de', 'es', 'fr', 'pt', 'ru', 'cn', 'tw']
            
            # 创建所有字段的列表，包括语言特定字段
            all_fields = base_fields.copy()
            for lang in languages:
                if lang != 'en':  # 'en' 已经包含在基本字段中
                    all_fields.extend([f'detail_{lang}', f'content_{lang}'])

            # 确保所有字段都存在，如果不存在则设置为 None
            for field in all_fields:
                if field not in data:
                    data[field] = None

            # 处理 'en' 的特殊情况
            if 'detail_en' in data:
                data['detail'] = data.pop('detail_en')
            if 'content_en' in data:
                data['content'] = data.pop('content_en')

            # 移除不匹配数据库模式的字段
            valid_data = {k: v for k, v in data.items() if k in all_fields}

            # if 'social_media' in data:
            #     for key, value in data['social_media'].items():
            #         if value:
            #             valid_data[key] = value
            #     del valid_data['social_media']

            response = self.supabase.table('web_navigation').insert(valid_data).execute()
            return response.data
        except Exception as e:
            print(f"Error inserting data: {e}")
            raise  # 重新抛出异常，以便重试装饰器捕获

    def update_website_data(self, url, data):
        try:
            response = self.supabase.table('websites').update(data).eq('url', url).execute()
            return response.data
        except Exception as e:
            print(f"Error updating data: {e}")
            return None