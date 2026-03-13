---
name: competitor-review-analyzer
description: 경쟁사 리뷰 분석 자동화. "경쟁사 분석", "한샘 리뷰 분석", "리뷰 크롤링", "competitor analysis", "다나와 리뷰", "상품 리뷰 수집", "리뷰 분석해줘" 등을 언급하거나 다나와 URL을 제공하면 자동 실행. 크롤링 → AI분석 → 인사이트 도출까지 전체 SOP 수행.
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
---

# 경쟁사 리뷰 분석 스킬

다나와 상품 리뷰를 수집하고, AI로 분석하여 인사이트와 액션 아이템까지 도출하는 End-to-End 자동화 스킬.

**전용 스크립트**: `scripts/danawa-reviews.py` (경량 크롤러 + 구글 시트)

## 전체 워크플로우

```
[1] 입력 확인 (URL 또는 상품명)
       ↓
[2] danawa-reviews.py로 리뷰 크롤링
       ↓
[3] 구글 시트 업로드 (선택)
       ↓
[4] AI 분석 (긍정/부정/키워드)
       ↓
[5] 인사이트 도출
       ↓
[6] 액션 아이템 제안
       ↓
[7] 마크다운 리포트 생성
```

---

## Step 1: 입력 확인

### 다나와 URL이 제공된 경우
URL에서 `pcode=` 값 추출:
```
https://prod.danawa.com/info/?pcode=6268026
                                    ^^^^^^^^
                                    상품코드
```

### 상품명만 제공된 경우
1. 다나와에서 상품 검색 (WebSearch 사용)
2. 가장 관련성 높은 상품의 pcode 확인
3. 사용자에게 확인 요청

---

## Step 2: 리뷰 크롤링 (danawa-reviews.py)

### 크롤링 실행

**크롤링 실행:**
```bash
cd .claude/skills/competitor-review-analyzer/scripts && \
python3 danawa-reviews.py <PRODUCT_CODE>
```

> 현재 워크스페이스 루트에서 실행하세요.

**구글 시트 업로드 포함:**
```bash
python3 danawa-reviews.py <PRODUCT_CODE> --sheet "https://docs.google.com/spreadsheets/d/xxx"
```

### 크롤링 특징
- **Firecrawl v2**: JavaScript 렌더링 지원 (동적 리뷰 로드)
- **경량 버전**: OCR 없이 텍스트만 빠르게 추출
- **JSON 출력**: 구조화된 데이터로 분석 용이
- **구글 시트**: 선택적 자동 업로드

### 예상 결과
- `/tmp/danawa_reviews_<pcode>_<timestamp>.json`
- 리뷰 텍스트 + 글자수 + 수집일시

---

## Step 3: 리뷰 데이터 추출

크롤링된 마크다운 파일에서 리뷰 추출:

```bash
# 크롤링 결과 읽기
cat /tmp/<브랜드>-<상품명>-reviews.md
```

### 리뷰 패턴 식별
- 리뷰 섹션: "후기", "리뷰", "별점" 키워드 이후
- 리뷰 내용: 20자 이상, 한글 포함
- 제외: URL, 메뉴, 배송비 안내 등

---

## Step 4: AI 분석

수집된 리뷰를 분석하여 다음 항목 도출:

### 4.1 감성 분류
각 리뷰를 분류:
- **긍정**: 만족, 추천, 좋아요, 튼튼 등
- **부정**: 불만, 아쉬움, 별로, 실망 등
- **중립**: 객관적 설명, 배송 언급만 등

### 4.2 키워드 추출
빈도 높은 키워드 Top 10:
- 품질 관련: 튼튼, 견고, 마감
- 조립 관련: 쉬움, 어려움, 시간
- 배송 관련: 빠름, 느림, 파손
- 가격 관련: 가성비, 비쌈, 저렴

### 4.3 불만 유형 분류
| 불만 유형 | 비율 | 대표 리뷰 |
|----------|------|----------|
| 조립 난이도 | 25% | "설명서가 불친절..." |
| 품질 문제 | 18% | "틈이 벌어져요..." |
| 배송 이슈 | 12% | "파손되어 왔어요..." |
| 냄새 | 8% | "처음엔 냄새가..." |

### 분석 프롬프트
분석 시 `templates/analysis_prompt.md` 참조

---

## Step 5: 인사이트 도출

### 경쟁사 강점 분석
```markdown
## 왜 잘 팔리나?
1. [가격] 10만원대 접근성
2. [브랜드] 한샘 신뢰도
3. [리뷰] 1만개+ 사회적 증거
4. [옵션] DIY/시공 선택 가능
```

### 경쟁사 약점 = 우리 기회
```markdown
## 우리의 기회
1. [조립 불만 25%] → 설치 서비스 차별화
2. [틈 벌어짐 18%] → 품질 정밀함 강조
3. [냄새 8%] → 친환경 E0 등급 마케팅
```

---

## Step 6: 액션 아이템

### 마케팅 메시지 제안
| 경쟁사 약점 | 우리 강점 | 메시지 제안 |
|------------|----------|------------|
| 조립 스트레스 | 무료 설치 | "설치까지 완벽하게" |
| 품질 불균일 | 정밀 품질관리 | "틈 없는 정밀함" |
| 화학 냄새 | 친환경 소재 | "냄새 없는 친환경" |

### 상세페이지 개선점
- [ ] 경쟁사 불만 TOP 3에 대한 우리 해결책 명시
- [ ] 설치 서비스 강조 배너
- [ ] 품질 테스트 인증 마크

### 리뷰 응대 전략
- 긍정 리뷰: 감사 + 재구매 유도
- 부정 리뷰: 해결책 제시 + CS 연결

---

## Step 7: 리포트 생성

### 저장 위치
```
./10-projects/{프로젝트명}/competitor-analysis/
```
> 프로젝트에 맞게 경로를 조정하세요.

### 파일명 형식
```
{브랜드}-{상품명}-review-analysis-{YYYYMMDD}.md
```

### 리포트 구조
```markdown
# [브랜드] [상품명] 리뷰 분석 리포트

## 1. 상품 개요
## 2. 리뷰 통계
## 3. 감성 분석
## 4. 키워드 분석
## 5. 불만 유형
## 6. 경쟁사 강점/약점
## 7. 우리의 기회
## 8. 액션 아이템
## 9. 부록: 원본 리뷰 샘플
```

---

## 사용 예시

### 예시 1: URL 제공
```
사용자: "이 상품 리뷰 분석해줘 https://prod.danawa.com/info/?pcode=6268026"

Claude:
1. pcode=6268026 추출
2. 크롤링 실행 (50페이지)
3. 구글 시트 업로드
4. AI 분석 수행
5. 리포트 생성
6. 인사이트 및 액션 아이템 제시
```

### 예시 2: 상품명 제공
```
사용자: "한샘 샘 책장 5단 경쟁사 분석해줘"

Claude:
1. 다나와에서 "한샘 샘 책장 5단" 검색
2. 상품 확인 요청 (여러 결과 시)
3. 확정 후 전체 SOP 실행
```

### 예시 3: 자사 관점 분석
```
사용자: "경쟁사 책장 리뷰 분석해서 우리 마케팅에 활용할 포인트 찾아줘"

Claude:
1. 크롤링 + 분석 수행
2. 자사 관점 기회/위협 특별 강조
3. 마케팅 메시지 및 상세페이지 개선안 제안
```

---

## 트러블슈팅

### 크롤링 실패
```bash
# .env 파일 확인
cat .claude/skills/competitor-review-analyzer/scripts/.env

# API 키 설정 필요
FIRECRAWL_API_KEY=your_key
```

### 구글 시트 업로드 실패
```bash
# 서비스 계정 JSON 파일 필요
~/.config/gspread/service_account.json

# 또는 환경변수로 지정
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service_account.json

# 시트에 서비스 계정 이메일 공유 필요!
```

### 리뷰가 적게 수집됨
- 다나와 상품 페이지 직접 확인
- 다른 pcode인지 확인
- Firecrawl wait_for 시간 조정

---

## 의존성

- **필요 API**: Firecrawl (https://firecrawl.dev)
- **필요 패키지**: `pip install firecrawl-py gspread google-auth python-dotenv`
- **구글 시트 (선택)**: 서비스 계정 JSON 필요

## 파일 구조

```
competitor-review-analyzer/
├── SKILL.md                    # 이 파일 (SOP)
├── scripts/
│   ├── danawa-reviews.py       # 리뷰 수집 + 구글 시트
│   └── .env                    # API 키 (FIRECRAWL_API_KEY)
└── templates/
    └── analysis_prompt.md      # AI 분석 프롬프트 템플릿
```

---

## 버전 히스토리

- **v2.0.0 (2025-12-07)**: 전용 경량 스크립트 도입
  - danawa-reviews.py: OCR 없이 텍스트만 빠르게 추출
  - 구글 시트 자동 업로드 기능 추가
  - JSON 구조화 출력
- **v1.1.0 (2025-12-07)**: web-crawler-ocr 스킬 통합
- **v1.0.0 (2025-12-07)**: 초기 스킬 생성
