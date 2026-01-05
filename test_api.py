import os
from dotenv import load_dotenv

load_dotenv()

print("=== 환경 변수 확인 ===")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')[:20]}..." if os.getenv('OPENAI_API_KEY') else "OPENAI_API_KEY: None")
print(f"TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}..." if os.getenv('TELEGRAM_BOT_TOKEN') else "TELEGRAM_BOT_TOKEN: None")
print(f"NOTION_API_KEY: {os.getenv('NOTION_API_KEY')[:20]}..." if os.getenv('NOTION_API_KEY') else "NOTION_API_KEY: None")
print()

# OpenAI 테스트
print("=== OpenAI API 테스트 ===")
try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    
    print("✅ OpenAI API 성공!")
    print(f"응답: {response.choices[0].message['content']}")
    
except Exception as e:
    print(f"❌ OpenAI API 실패!")
    print(f"에러: {e}")
    import traceback
    print(traceback.format_exc())