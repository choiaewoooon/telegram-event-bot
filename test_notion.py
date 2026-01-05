import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv('NOTION_API_KEY'))
db_id = os.getenv('NOTION_DATABASE_ID')

print("=== Notion 데이터베이스 속성 확인 ===")

try:
    # 데이터베이스 정보 가져오기
    db = notion.databases.retrieve(database_id=db_id)
    
    print("\n실제 컬럼명 목록:")
    for prop_name, prop_info in db['properties'].items():
        print(f"  - '{prop_name}' (타입: {prop_info['type']})")
    
    print("\n\n=== 테스트 페이지 생성 ===")
    
    # 간단한 테스트 페이지
    result = notion.pages.create(
        parent={"database_id": db_id},
        properties={
            "프로젝트명": {
                "title": [{"text": {"content": "테스트"}}]
            }
        }
    )
    
    print("✅ Notion 저장 성공!")
    print(f"페이지 URL: {result['url']}")
    
except Exception as e:
    print(f"❌ 에러: {e}")
    import traceback
    print(traceback.format_exc())