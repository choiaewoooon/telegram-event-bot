import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client

# 환경 변수 로드
load_dotenv()

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DB_ID = os.getenv('NOTION_DATABASE_ID')

notion = Client(auth=NOTION_API_KEY)


def update_end_dates():
    """기존 Notion 데이터베이스의 모든 항목에 종료일 추가"""

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

        # 이미 종료일이 있는지 확인
        has_end_date = False
        if '이벤트 종료일' in properties:
            end_date_data = properties['이벤트 종료일'].get('date')
            if end_date_data and end_date_data.get('start'):
                has_end_date = True

        if has_end_date:
            print(f"⏭️  [{event_title[:30]}] - 이미 종료일 존재, 건너뜀")
            skipped_count += 1
            continue

        # 시작일과 진행 기간 가져오기
        start_date = None
        if '이벤트 시작일' in properties:
            date_obj = properties['이벤트 시작일'].get('date')
            if date_obj:
                start_date = date_obj.get('start')

        duration_days = None
        if '이벤트 진행 기간' in properties:
            duration_days = properties['이벤트 진행 기간'].get('number')

        # 종료일 계산
        if start_date and duration_days:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=int(duration_days))
                end_date = end_dt.strftime("%Y-%m-%d")

                # Notion 업데이트
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        "이벤트 종료일": {
                            "date": {"start": end_date}
                        }
                    }
                )

                print(f"✅ [{event_title[:30]}] - 종료일 추가: {end_date}")
                updated_count += 1

            except Exception as e:
                print(f"❌ [{event_title[:30]}] - 오류: {e}")
                error_count += 1
        else:
            missing = []
            if not start_date:
                missing.append("시작일")
            if not duration_days:
                missing.append("진행 기간")
            print(f"⚠️  [{event_title[:30]}] - 누락된 데이터: {', '.join(missing)}")
            skipped_count += 1

    print(f"\n{'='*60}")
    print(f"📊 작업 완료!")
    print(f"   ✅ 업데이트됨: {updated_count}개")
    print(f"   ⏭️  건너뜀: {skipped_count}개")
    print(f"   ❌ 오류: {error_count}개")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("="*60)
    print("🚀 Notion 이벤트 종료일 일괄 업데이트 스크립트")
    print("="*60)
    print()

    confirm = input("⚠️  모든 이벤트에 종료일을 추가하시겠습니까? (y/n): ")

    if confirm.lower() == 'y':
        update_end_dates()
    else:
        print("❌ 작업이 취소되었습니다.")
