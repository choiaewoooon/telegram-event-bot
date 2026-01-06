import os
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI

# 환경 변수 로드
load_dotenv()

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DB_ID = os.getenv('NOTION_DATABASE_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

notion = Client(auth=NOTION_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_location(event_title: str, mission_content: str) -> str:
    """OpenAI로 이벤트 장소 구분"""

    prompt = f"""다음 이벤트 정보를 보고 온라인/오프라인 이벤트인지 판단하세요.

이벤트 제목: {event_title}
미션 내용: {mission_content}

규칙:
- 특정 오프라인 장소나 주소가 명시되어 있으면 "오프라인"
- 온라인에서만 진행되는 이벤트면 "온라인"
- 판단이 애매하면 기본값 "온라인"

"온라인" 또는 "오프라인" 중 하나만 응답하세요."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )

        result = response.choices[0].message.content.strip()

        # 응답에서 "온라인" 또는 "오프라인" 추출
        if "오프라인" in result:
            return "오프라인"
        else:
            return "온라인"

    except Exception as e:
        print(f"❌ AI 분석 실패: {e}")
        return "온라인"


def update_locations():
    """기존 Notion 데이터베이스의 모든 항목에 장소 정보 추가"""

    print("🔄 Notion 데이터베이스에서 데이터 가져오는 중...")

    # 모든 페이지 가져오기
    results = notion.databases.query(database_id=NOTION_DB_ID)
    pages = results.get('results', [])

    print(f"📊 총 {len(pages)}개의 이벤트를 찾았습니다.\n")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for page in pages:
        page_id = page['id']
        properties = page.get('properties', {})

        # 이벤트 제목 가져오기
        event_title = "제목 없음"
        if '이벤트 제목' in properties:
            title_data = properties['이벤트 제목'].get('title', [])
            if title_data and len(title_data) > 0:
                event_title = title_data[0].get('text', {}).get('content', '제목 없음')

        # 이미 장소가 있는지 확인
        has_location = False
        if '장소' in properties:
            location_data = properties['장소'].get('select')
            if location_data and location_data.get('name'):
                has_location = True

        if has_location:
            print(f"⏭️  [{event_title[:30]}] - 이미 장소 정보 존재, 건너뜀")
            skipped_count += 1
            continue

        # 미션 내용 가져오기
        mission_content = ""
        if '미션 내용' in properties:
            mission_data = properties['미션 내용'].get('rich_text', [])
            if mission_data and len(mission_data) > 0:
                mission_content = mission_data[0].get('text', {}).get('content', '')

        # AI로 장소 판단
        try:
            location = analyze_location(event_title, mission_content)

            # Notion 업데이트
            notion.pages.update(
                page_id=page_id,
                properties={
                    "장소": {
                        "select": {"name": location}
                    }
                }
            )

            emoji = "🌐" if location == "온라인" else "📍"
            print(f"✅ [{event_title[:30]}] - {emoji} {location}")
            updated_count += 1

        except Exception as e:
            print(f"❌ [{event_title[:30]}] - 오류: {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"📊 작업 완료!")
    print(f"   ✅ 업데이트됨: {updated_count}개")
    print(f"   ⏭️  건너뜀: {skipped_count}개")
    print(f"   ❌ 오류: {error_count}개")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("="*60)
    print("🚀 Notion 이벤트 장소 일괄 업데이트 스크립트")
    print("="*60)
    print()

    confirm = input("⚠️  모든 이벤트에 장소 정보를 추가하시겠습니까? (y/n): ")

    if confirm.lower() == 'y':
        update_locations()
    else:
        print("❌ 작업이 취소되었습니다.")
