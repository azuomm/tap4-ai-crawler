import os
from dotenv import load_dotenv
from groq import Groq
import logging
from transformers import LlamaTokenizer
from util.common_util import CommonUtil

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
util = CommonUtil()
# 初始化LLaMA模型的Tokenizer
tokenizer = LlamaTokenizer.from_pretrained("huggyllama/llama-65b")

class LLMUtil:
    def __init__(self):
        load_dotenv()
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        logger.info(f"Groq API Key:{self.groq_api_key}")
        self.detail_sys_prompt = os.getenv('DETAIL_SYS_PROMPT')
        self.tag_selector_sys_prompt = os.getenv('TAG_SELECTOR_SYS_PROMPT')
        self.language_sys_prompt = os.getenv('LANGUAGE_SYS_PROMPT')
        self.groq_model = os.getenv('GROQ_MODEL')
        self.groq_max_tokens = int(os.getenv('GROQ_MAX_TOKENS', 5000))
        self.client = Groq(
            api_key=self.groq_api_key
        )
        self.description_translation_prompt = os.getenv('DESCRIPTION_TRANSLATION_PROMPT')
        self.description_translation_prompt_zh = os.getenv('DESCRIPTION_TRANSLATION_PROMPT_ZH')
        self.description_translation_prompt_jp = os.getenv('DESCRIPTION_TRANSLATION_PROMPT_JP')
        self.description_translation_prompt_tw = os.getenv('DESCRIPTION_TRANSLATION_PROMPT_TW')

    def process_detail(self, user_prompt):
        logger.info("正在处理Detail...")
        return util.detail_handle(self.process_prompt(self.detail_sys_prompt, user_prompt))

    def process_tags(self, user_prompt):
        logger.info(f"正在处理tags...")
        result = self.process_prompt(self.tag_selector_sys_prompt, user_prompt)
        # 将result（逗号分割的字符串）转为数组
        if result:
            tags = [element.strip() for element in result.split(',')]
        else:
            tags = []
        logger.info(f"tags处理结果:{tags}")
        return tags

    def process_language(self, language, content):
        logger.info(f"正在处理多语言:{language}")
        if language.lower() == 'english':
            return content
        
        if language.lower() == 'simplified chinese':
            user_prompt = self.description_translation_prompt_zh
        elif language.lower() == 'Traditional Chinese':
            user_prompt = self.description_translation_prompt_tw    
        elif language.lower() == 'japanese':
            user_prompt = self.description_translation_prompt_jp
        else:
            user_prompt = self.description_translation_prompt.replace("{language}", language)
        
        result = self.process_prompt(user_prompt, content)
        
        if not result or len(result.strip()) < 10:  # Assuming a valid translation should be at least 10 characters
            logger.warning(f"Translation to {language} failed or returned invalid result. Returning original content.")
            return content
        
        if not content.startswith("#"):
            result = result.replace("### ", "").replace("## ", "").replace("# ", "").replace("**", "")
        
        logger.info(f"user_prompt:{user_prompt}")
        logger.info(f"!!!!多语言:{language}, 【翻译结果:】{result}")
        return result

    def process_languages(self, content):
        languages = {
            'en': 'English',
            'jp': 'Japanese',
            'de': 'German',
            'es': 'Spanish',
            'fr': 'French',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'cn': 'Simplified Chinese',
            'tw': 'Traditional Chinese'
        }
        
        results = {}
        for lang_code, lang_name in languages.items():
            if lang_code == 'en':
                results[f'detail_{lang_code}'] = content
            else:
                translated_content = self.process_language(lang_name, content)
                results[f'detail_{lang_code}'] = translated_content
        
        return results

    def process_prompt(self, prompt, websiteContent):
        if not prompt:
            logger.info(f"LLM无需处理，sys_prompt为空:{prompt}")
            return None
        if not websiteContent:
            logger.info(f"LLM无需处理，user_prompt为空:{websiteContent}")
            return None

        logger.info(f"LLM正在处理。。。:{prompt}")
        try:
            tokens = tokenizer.encode(websiteContent)
            if len(tokens) > self.groq_max_tokens:
                logger.info(f"用户输入长度超过{self.groq_max_tokens}，进行截取")
                truncated_tokens = tokens[:self.groq_max_tokens]
                websiteContent = tokenizer.decode(truncated_tokens)

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": websiteContent,
                    }
                ],
                model=self.groq_model,
                temperature=0.2,
            )
            if chat_completion.choices[0] and chat_completion.choices[0].message:
                logger.info(f"LLM完成处理，成功响应!")
                return chat_completion.choices[0].message.content
            else:
                logger.info("LLM完成处理，处理结果为空")
                return None
        except Exception as e:
            logger.error(f"LLM处理失败", e)
            return None

    def translate_description(self, description):
        languages = {
            'en': 'English',
            'jp': 'Japanese',
            'de': 'German',
            'es': 'Spanish',
            'fr': 'French',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'cn': 'Simplified Chinese',
            'tw': 'Traditional Chinese'
        }
        
        results = {}
        for lang_code, lang_name in languages.items():
            if lang_code == 'en':
                results[f'content_{lang_code}'] = description
            else:
                translated_content = self.process_language(lang_name, description)
                results[f'content_{lang_code}'] = translated_content
        
        return results