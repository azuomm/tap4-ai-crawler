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
            response = self.supabase.table('web_navigation').insert(data).execute()
            return response.data
        except Exception as e:
            print(f"Error inserting data: {e}")
            raise  # 重新抛出异常，让重试装饰器捕获

    def update_website_data(self, url, data):
        try:
            response = self.supabase.table('websites').update(data).eq('url', url).execute()
            return response.data
        except Exception as e:
            print(f"Error updating data: {e}")
            return None