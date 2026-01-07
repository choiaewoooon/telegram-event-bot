# 텔레그램 이벤트 분석 봇

크립토/블록체인 이벤트 정보를 자동으로 수집하고 Notion에 저장하는 봇

만든 이유는 데이터 적재를 위함이며, 이벤트 참여에 목적을 두고 있지 않음 그러니 이걸 통해서 "이벤트 놓치지 말아야지" 보다는? 
"이런이런 이벤트들이 있었구나!"가 적절한 목적이 되지 않을까 생각이 듦.  

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

알아서 데이터를 적재할 노션 페이지를 만들어 된다는 뜻임. 노션 데이터 베이스 없으면 봇이 입력을 못하겠지요? 

(노션 데이터 베이스 각 행 설정, 1번이 첫번째 행, 큰따옴표는 글씨이며 괄호는 유형) 

1. "이벤트 제목"(기본)
2. "프로젝트명"(Text)
3. "총 상금"(Text)
4. "회차별 상금"(Text)
5. "상금 가치"(Number)
6. "이벤트 시작일"(Date) - 시작일/종료일 통합 (종료일 있으면 자동으로 날짜 범위 표시)
7. "이벤트 진행 기간"(Number)
8. "미션 내용"(Text)
9. "장소"(Select: 온라인, 오프라인)
10. "원본 링크"(URL)

## 나머지 .py 자료의 목적

1. update_end_dates.py : 기존 자료를 새 날짜 형식(start/end 통합)으로 마이그레이션
2. update_locations.py : 기존 자료에 온/오프라인 여부 일괄 적용

## 버전 히스토리

- v3.2 : 이벤트 시작일/종료일 통합 (Notion Date 필드 하나로 범위 표시)
- v3.1 : 장소 구분 추가 (온라인/오프라인)
- v3.0 : 기본 기능 완성
