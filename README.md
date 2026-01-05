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

## 노션(notion) 데이터 베이스 설정 

(노션 데이터 베이스 각 행 설정, 1번이 첫번째 행, 큰따옴표는 글씨이며 괄호는 유형) 

1. "이벤트 제목"(기본)
2. "프로젝트명"(Text)
3. "총 상금"(Text)
4. "회차별 상금"(Text)
5. "상금 가치"(Number)
6. "이벤트 시작일"(date)
7. "이벤트 진행 기간"(date)