# 텔레그램 이벤트 분석 봇

크립토/블록체인 이벤트 정보를 자동으로 수집하고 Notion에 저장하는 봇

## 기능

- 텔레그램 메시지 수신
- OpenAI로 이벤트 정보 추출
- Notion 데이터베이스에 자동 저장

## 설치
```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일 생성:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_token
OPENAI_API_KEY=your_openai_key
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id
```

## 실행
```bash
python main.py
```

## 사용법

1. 텔레그램 봇에게 `/start` 전송
2. 이벤트 메시지 전송
3. 자동으로 분석 & Notion에 저장
