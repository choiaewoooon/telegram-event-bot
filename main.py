import os
import logging
import re
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from notion_client import Client

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API 설정
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DB_ID = os.getenv('NOTION_DATABASE_ID')

# Notion 클라이언트
notion = Client(auth=NOTION_API_KEY)


def analyze_event(text: str) -> dict:
    """OpenAI로 이벤트 메시지 분석"""
    from openai import OpenAI
    
    prompt = f"""다음은 크립토/블록체인 이벤트 메시지입니다.

<메시지>
{text}
</메시지>

이벤트 정보를 정확히 추출하여 JSON으로만 응답하세요:

{{
  "event_title": "이벤트 제목 (프로젝트명 + 핵심 내용, 예: PlayKami 신년맞이 이벤트)",
  "project_name": "프로젝트명만 (예: PlayKami, Rootstock)",
  "total_prize": "총 상금이 명시되어 있으면 기입, 없으면 '총 상금 통일'",
  "prize_per_round": "회차별/등수별 상금 상세 (예: 1등 30000 $CROSS, 2등 15000 $CROSS)",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "duration_days": 이벤트 진행 일수,
  "mission_content": "유저가 수행해야 할 미션을 간단명료하게 정리 (예: 트위터 팔로우, 텔레그램 가입, 댓글 작성)"
}}

규칙:
1. event_title: 매력적이고 명확한 제목 생성
2. project_name: 프로젝트명만 간단히
3. total_prize:
   - 전체 상금이 명시되어 있으면 작성 (예: 5천만원, 총 150000 $CROSS)
   - 회차별로만 나뉘어 있고 전체 합계가 없으면 "총 상금 통일"
4. prize_per_round: 각 회차/등수별 상금을 자세히
5. start_date: YYYY-MM-DD (현재 2026년 1월)
6. end_date: YYYY-MM-DD (시작일 + 진행일수로 계산)
7. duration_days: 시작일~종료일 일수
8. mission_content: 유저가 해야 할 행동을 핵심만 간단히 (2-3줄 이내)
9. JSON만 출력

JSON:"""

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        result = response.choices[0].message.content.strip()
        
        if '```json' in result:
            result = result.split('```json')[1].split('```')[0]
        elif '```' in result:
            result = result.split('```')[1].split('```')[0]
        
        parsed = json.loads(result.strip())
        logger.info(f"✅ AI 분석: {parsed}")
        return parsed
    
    except Exception as e:
        logger.error(f"❌ AI 분석 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "event_title": "분석 실패",
            "project_name": "미확인",
            "total_prize": "N/A",
            "prize_per_round": "N/A",
            "start_date": None,
            "end_date": None,
            "duration_days": None,
            "mission_content": "N/A"
        }


def check_duplicate(url: str, project_name: str, start_date: str) -> bool:
    """Notion에서 중복 이벤트 확인"""
    try:
        logger.info(f"🔍 중복 확인 시작...")
        
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            page_size=100
        )
        
        for page in results.get('results', []):
            properties = page.get('properties', {})
            
            if '원본 링크' in properties:
                existing_url = properties['원본 링크'].get('url')
                if existing_url and url and existing_url == url:
                    logger.warning(f"⚠️ 중복 감지: 동일한 원본 링크 - {url}")
                    return True
            
            if project_name and start_date:
                existing_project = None
                if '프로젝트명' in properties:
                    project_rich = properties['프로젝트명'].get('rich_text', [])
                    if project_rich and len(project_rich) > 0:
                        existing_project = project_rich[0].get('text', {}).get('content', '')
                
                existing_date = None
                if '이벤트 시작일' in properties:
                    date_obj = properties['이벤트 시작일'].get('date')
                    if date_obj:
                        existing_date = date_obj.get('start')
                
                if existing_project and existing_date:
                    if existing_project == project_name and existing_date == start_date:
                        logger.warning(f"⚠️ 중복 감지: {project_name} - {start_date}")
                        return True
        
        logger.info("✅ 중복 없음 - 신규 이벤트")
        return False
    
    except Exception as e:
        logger.error(f"❌ 중복 확인 실패: {e}")
        return False


def save_to_notion(url: str, data: dict) -> bool:
    """Notion 데이터베이스에 저장"""
    try:
        properties = {
            "이벤트 제목": {
                "title": [{"text": {"content": str(data.get("event_title", "미확인"))[:100]}}]
            }
        }
        
        logger.info(f"1️⃣ 이벤트 제목: {data.get('event_title')}")
        
        project = str(data.get("project_name", "")).strip()
        if project and project not in ["N/A", "None", ""]:
            properties["프로젝트명"] = {
                "rich_text": [{"text": {"content": project[:100]}}]
            }
            logger.info(f"2️⃣ 프로젝트명: {project}")
        
        if url and url not in ["URL 없음", "개인 메시지 (링크 없음)", "비공개 채널"]:
            if url.startswith("http"):
                properties["원본 링크"] = {"url": url[:2000]}
                logger.info(f"3️⃣ 원본 링크: {url[:50]}")
        
        total_prize = str(data.get("total_prize", "")).strip()
        if total_prize and total_prize not in ["N/A", "None", "", "총 상금 통일"]:
            properties["총 상금"] = {
                "rich_text": [{"text": {"content": total_prize[:2000]}}]
            }
            logger.info(f"4️⃣ 총 상금: {total_prize[:50]}")
        elif total_prize == "총 상금 통일":
            properties["총 상금"] = {
                "rich_text": [{"text": {"content": "총 상금 통일"}}]
            }
            logger.info(f"4️⃣ 총 상금: 통일")
        
        per_round = str(data.get("prize_per_round", "")).strip()
        if per_round and per_round not in ["N/A", "None", ""]:
            properties["회차별 상금"] = {
                "rich_text": [{"text": {"content": per_round[:2000]}}]
            }
            logger.info(f"5️⃣ 회차별 상금: {per_round[:50]}")
        
        start_date = data.get("start_date")
        if start_date:
            start_str = str(start_date).strip()
            if start_str and start_str not in ["None", "null", "N/A", ""]:
                properties["이벤트 시작일"] = {
                    "date": {"start": start_str}
                }
                logger.info(f"6️⃣ 이벤트 시작일: {start_str}")

        end_date = data.get("end_date")
        if end_date:
            end_str = str(end_date).strip()
            if end_str and end_str not in ["None", "null", "N/A", ""]:
                properties["이벤트 종료일"] = {
                    "date": {"start": end_str}
                }
                logger.info(f"7️⃣ 이벤트 종료일: {end_str}")

        duration = data.get("duration_days")
        if duration is not None:
            try:
                duration_num = int(duration) if duration else None
                if duration_num:
                    properties["이벤트 진행 기간"] = {"number": duration_num}
                    logger.info(f"8️⃣ 이벤트 진행 기간: {duration_num}일")
            except (ValueError, TypeError):
                logger.warning(f"⚠️ 진행 기간 변환 실패: {duration}")

        mission = str(data.get("mission_content", "")).strip()
        if mission and mission not in ["N/A", "None", ""]:
            properties["미션 내용"] = {
                "rich_text": [{"text": {"content": mission[:2000]}}]
            }
            logger.info(f"9️⃣ 미션 내용: {mission[:50]}")

        result = notion.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties=properties
        )
        
        logger.info(f"✅ Notion 저장 성공: {result['id']}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Notion 저장 실패: {e}")
        import traceback
        logger.error(f"상세:\n{traceback.format_exc()}")
        return False


async def process_single_event(text: str, url: str) -> dict:
    """단일 이벤트 처리"""
    result = analyze_event(text)

    is_duplicate = check_duplicate(
        url=url if url not in ["URL 없음", "비공개 채널"] else None,
        project_name=result.get("project_name"),
        start_date=result.get("start_date")
    )

    if is_duplicate:
        return {
            "status": "duplicate",
            "result": result,
            "url": url
        }

    success = save_to_notion(url, result)

    return {
        "status": "success" if success else "error",
        "result": result,
        "url": url
    }


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """텔레그램 메시지 처리"""
    message = update.message

    is_forwarded = message.forward_origin is not None

    if is_forwarded:
        logger.info("📬 포워딩 메시지")
        origin = message.forward_origin

        url = None
        if hasattr(origin, 'chat') and hasattr(origin.chat, 'username'):
            chat_username = origin.chat.username
            message_id = origin.message_id
            url = f"https://t.me/{chat_username}/{message_id}"
            logger.info(f"🔗 {url}")
        else:
            url = "비공개 채널"

        text = message.text or message.caption or ""
        if message.photo:
            text += "\n[이미지 포함]"

        # 포워딩 메시지는 단일 이벤트로 처리
        processing = await message.reply_text("🔄 분석 중...")

        process_result = await process_single_event(text, url)

        if process_result["status"] == "duplicate":
            result = process_result["result"]
            await processing.edit_text(
                "⚠️ 사전에 등록 된 이벤트 입니다.\n\n"
                f"📋 이벤트: {result.get('event_title', 'N/A')}\n"
                f"🏢 프로젝트: {result.get('project_name', 'N/A')}\n"
                f"📅 시작일: {result.get('start_date', 'N/A')}"
            )
            logger.info("⚠️ 중복 이벤트로 저장하지 않음")
            return

        result = process_result["result"]
        if process_result["status"] == "success":
            duration = f"{result.get('duration_days', 'N/A')}일" if result.get('duration_days') else 'N/A'
            total_info = result.get('total_prize', 'N/A')

            mission_text = result.get('mission_content', 'N/A')
            if len(mission_text) > 80:
                mission_text = mission_text[:80] + "..."

            response_text = (
                f"✅ 분석 완료!\n\n"
                f"📋 이벤트: {result.get('event_title', 'N/A')}\n"
                f"🏢 프로젝트: {result.get('project_name', 'N/A')}\n"
                f"💰 총 상금: {total_info}\n"
                f"🎁 회차별: {result.get('prize_per_round', 'N/A')[:60]}...\n"
                f"📅 시작: {result.get('start_date', 'N/A')}\n"
                f"🏁 종료: {result.get('end_date', 'N/A')}\n"
                f"⏱️ 기간: {duration}\n"
                f"🎯 미션: {mission_text}\n"
                f"💵 가치: 수동 입력 필요"
            )
            if url and url not in ["URL 없음", "비공개 채널"]:
                response_text += f"\n🔗 {url}"
        else:
            response_text = "❌ 저장 실패"

        await processing.edit_text(response_text)

    else:
        # 일반 메시지: 여러 링크 처리 가능
        logger.info("💬 일반 메시지")
        text = message.text or message.caption or ""

        # 줄바꿈으로 구분된 링크들 추출
        lines = text.strip().split('\n')
        urls = []
        for line in lines:
            line_urls = re.findall(r'https?://[^\s]+', line.strip())
            if line_urls:
                urls.extend(line_urls)

        if not urls:
            # 링크가 없으면 전체 텍스트를 하나의 이벤트로 처리
            urls = ["URL 없음"]

        processing = await message.reply_text(f"🔄 {len(urls)}개 이벤트 분석 중...")

        # 각 링크마다 처리
        results = []
        for idx, url in enumerate(urls, 1):
            logger.info(f"📌 [{idx}/{len(urls)}] 처리 중: {url[:50] if url != 'URL 없음' else 'URL 없음'}")
            process_result = await process_single_event(text, url)
            results.append(process_result)

        # 결과 요약
        success_count = sum(1 for r in results if r["status"] == "success")
        duplicate_count = sum(1 for r in results if r["status"] == "duplicate")
        error_count = sum(1 for r in results if r["status"] == "error")

        response_lines = [f"📊 처리 완료 ({len(urls)}개)"]
        response_lines.append(f"✅ 저장: {success_count}개")
        if duplicate_count > 0:
            response_lines.append(f"⚠️ 중복: {duplicate_count}개")
        if error_count > 0:
            response_lines.append(f"❌ 실패: {error_count}개")

        response_lines.append("")

        # 각 결과 상세
        for idx, process_result in enumerate(results, 1):
            result = process_result["result"]
            status_emoji = "✅" if process_result["status"] == "success" else "⚠️" if process_result["status"] == "duplicate" else "❌"
            response_lines.append(
                f"{status_emoji} [{idx}] {result.get('event_title', 'N/A')[:30]}"
            )

        await processing.edit_text("\n".join(response_lines))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작"""
    await update.message.reply_text(
        "🤖 이벤트 분석 봇 v3.0 (최신 OpenAI)\n\n"
        "📤 채널 게시물을 포워딩하세요!\n"
        "🤖 AI가 자동 분석\n"
        "📊 Notion에 저장\n\n"
        "✨ 주요 기능:\n"
        "- 이벤트 제목 자동 생성\n"
        "- 총 상금 조건부 표시\n"
        "- 회차별 상금 상세 분석\n"
        "- 중복 이벤트 확인\n"
        "- 상금 가치는 수동 입력"
    )


def main():
    """실행"""
    if not all([TELEGRAM_TOKEN, NOTION_DB_ID, OPENAI_API_KEY]):
        logger.error("❌ 환경 변수 누락")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.FORWARDED, handle_message))
    
    logger.info("🚀 봇 시작 v3.1 (다수 링크 저장)")
    app.run_polling()


if __name__ == '__main__':
    main()