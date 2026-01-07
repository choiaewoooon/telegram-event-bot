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
    """기존 Notion 데이터베이스의 이벤트 시작일을 start/end 통합 형식으로 변환"""

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

        # 시작일 가져오기
        start_date = None
        has_end_in_start = False
        if '이벤트 시작일' in properties:
            date_obj = properties['이벤트 시작일'].get('date')
            if date_obj:
                start_date = date_obj.get('start')
                # 이미 end가 설정되어 있는지 확인
                if date_obj.get('end'):
                    has_end_in_start = True

        if has_end_in_start:
            print(f"⏭️  [{event_title[:30]}] - 이미 종료일 통합됨, 건너뜀")
            skipped_count += 1
            continue

        # 종료일 가져오기 (별도 필드에서)
        end_date = None
        if '이벤트 종료일' in properties:
            end_date_obj = properties['이벤트 종료일'].get('date')
            if end_date_obj:
                end_date = end_date_obj.get('start')

        # 종료일이 없으면 진행 기간으로 계산
        if not end_date and start_date:
            duration_days = None
            if '이벤트 진행 기간' in properties:
                duration_days = properties['이벤트 진행 기간'].get('number')

            if duration_days:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = start_dt + timedelta(days=int(duration_days))
                    end_date = end_dt.strftime("%Y-%m-%d")
                except Exception as e:
                    print(f"⚠️  [{event_title[:30]}] - 종료일 계산 실패: {e}")

        # 이벤트 시작일에 start/end 통합
        if start_date:
            try:
                date_property = {"start": start_date}

                if end_date and end_date != start_date:
                    date_property["end"] = end_date
                    print(f"✅ [{event_title[:30]}] - 날짜 통합: {start_date} → {end_date}")
                else:
                    print(f"✅ [{event_title[:30]}] - 단일 날짜: {start_date}")

                # Notion 업데이트
                notion.pages.update(
                    page_id=page_id,
                    properties={
                        "이벤트 시작일": {
                            "date": date_property
                        }
                    }
                )

                updated_count += 1

            except Exception as e:
                print(f"❌ [{event_title[:30]}] - 오류: {e}")
                error_count += 1
        else:
            print(f"⚠️  [{event_title[:30]}] - 시작일 없음, 건너뜀")
            skipped_count += 1

    print(f"\n{'='*60}")
    print(f"📊 작업 완료!")
    print(f"   ✅ 업데이트됨: {updated_count}개")
    print(f"   ⏭️  건너뜀: {skipped_count}개")
    print(f"   ❌ 오류: {error_count}개")
    print(f"{'='*60}")
    print(f"\n💡 이제 Notion에서 '이벤트 종료일' 열을 삭제해도 됩니다.")


if __name__ == '__main__':
    print("="*60)
    print("🚀 Notion 이벤트 날짜 통합 스크립트 (v3.2)")
    print("="*60)
    print()
    print("📌 이 스크립트는 다음을 수행합니다:")
    print("   1. '이벤트 시작일' 필드에 start/end를 통합")
    print("   2. '이벤트 종료일' 필드의 데이터를 가져와 통합")
    print("   3. 종료일이 없으면 '진행 기간'으로 자동 계산")
    print()
    print("⚠️  실행 후 '이벤트 종료일' 열은 수동으로 삭제하셔야 합니다.")
    print()

    confirm = input("계속 진행하시겠습니까? (y/n): ")

    if confirm.lower() == 'y':
        update_end_dates()
    else:
        print("❌ 작업이 취소되었습니다.")
