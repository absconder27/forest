---
name: web-crawler-ocr
description: 웹페이지 크롤링 + 이미지 OCR 자동 분석. "이 URL 분석해줘", "크롤링해줘", "웹사이트 분석", "사이트 크롤링", "경쟁사 분석", "페이지 추출", "analyze this URL", "crawl website", "competitor analysis", "extract webpage" 등을 언급하거나 https:// 또는 http:// URL을 제공하면 자동 실행. Claude의 5MB 이미지 제한을 Gemini OCR(20MB)로 우회.
context: fork
allowed-tools:
  - Bash
  - Read
  - Write
---

# Web Crawler + Gemini OCR Skill

Extract complete web page content (text + images) and save as markdown file.

## When to Use This Skill

This skill automatically activates when the user:
- Provides a URL: "https://example.com analyze this"
- Requests web crawling: "crawl this website", "extract webpage content"
- Mentions competitor analysis: "analyze competitor site"
- Needs image OCR from web: "OCR images from this page"
- Wants to bypass 5MB limit: "large images on this site"

## What This Skill Does

1. **Firecrawl**: Clean text extraction (removes ads/clutter)
2. **Gemini OCR**: Extract text from images (up to 20MB per image)
3. **Complete Markdown**: Text + image analysis in one file

## Instructions

### Step 1: Identify the URL
Extract URL(s) from user message:
- Look for `https://` or `http://`
- Multiple URLs? Process each one

### Step 2: Determine Output Location

Based on user context, choose appropriate path:

- **Competitor Analysis:** `50-resources/competitor-analysis/`
- **Educational Reference:** `10-projects/12-education/{project-folder}/`
- **General Web Research:** `50-resources/web-research/`

Resolve paths relative to the current workspace or PKM root. Ask the user if unclear.

**Filename:** Use domain + timestamp or user-specified name.

### Step 3: Execute Web Crawler Script

```bash
# 1. Install dependencies (first time only)
cd .claude/skills/web-crawler-ocr/scripts && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt

# 2. Run crawler
cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
python3 web-crawler.py "<URL>" "<output-path>"
```

**Important:**
- Always use full absolute paths
- Quote URLs to handle special characters
- Ensure output directory exists (create with `mkdir -p` if needed)
- Virtual env is created locally in scripts/ folder (not committed to git)

### Step 4: Read and Analyze Results

1. Use Read tool to open generated markdown file
2. Extract key insights
3. Summarize for user

### Step 5: OCR 재배치 (필수)

크롤링 결과 파일의 끝부분에 "📸 이미지 OCR 결과" 섹션이 있다면 **반드시** 본문의 적절한 위치로 재배치해야 합니다.

**재배치 프로세스:**

1. **파일 읽기 및 OCR 블록 확인**
   ```bash
   # Read tool로 크롤링된 마크다운 파일 열기
   # "## 📸 이미지 OCR 결과" 섹션이 있는지 확인
   ```

2. **각 OCR 블록 분석**
   - "### 이미지 N" 블록 순서대로 처리
   - 각 블록의 OCR 내용과 이미지 URL 추출

3. **본문에서 이미지 위치 찾기**
   - 본문에서 해당 이미지 URL이 포함된 마크다운 링크 찾기: `[![](이미지URL)]`
   - 이미지 바로 아래에 OCR 블록 삽입

4. **OCR 블록 삽입 형식**
   ```markdown
   [![](이미지URL)](...)

   ---

   **[이미지: ALT 텍스트]**

   ```
   OCR 추출 내용
   ```

   ---

   (본문 계속...)
   ```

5. **끝의 OCR 섹션 제거**
   - 모든 OCR 블록이 재배치되었으면
   - "## 📸 이미지 OCR 결과" 전체 섹션 삭제

6. **파일 저장 및 확인**
   - Edit tool로 변경사항 저장
   - 사용자에게 "OCR 블록 N개를 본문의 적절한 위치로 재배치했습니다" 보고

**매칭 로직:**
- 이미지 URL로 정확히 매칭
- 이미지 마크다운: `![...](URL)` 또는 `[![...](URL)]`
- OCR 블록의 "이미지 URL" 필드와 본문의 이미지 URL 비교

**예시:**

본문에서 찾은 이미지:
```markdown
[![](https://example.com/image1.png)](https://example.com/image1.png)
```

OCR 섹션:
```markdown
### 이미지 1
**이미지 URL**: `https://example.com/image1.png`
**OCR 추출 내용**:
```
텍스트 내용...
```
```

→ 이미지 바로 아래에 OCR 블록 삽입

### Step 6: Suggest Next Steps

- Additional URLs to analyze?
- Comparative analysis needed?
- PKM organization suggestions?

## Examples

### Example 1: Competitor Cafe Analysis

**User:** "Analyze this competitor cafe website: https://competitor-cafe.com"

**Claude Actions:**
```bash
# 1. Ensure directory exists
mkdir -p <PKM_ROOT>/50-resources/competitor-analysis

# 2. Run crawler
cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
python3 web-crawler.py \
    "https://competitor-cafe.com" \
    <PKM_ROOT>/50-resources/competitor-analysis/competitor-cafe-20251029.md

# 3. Read results (use Read tool)
# 4. Provide analysis
```

**Response:**
"Crawled competitor website successfully. Extracted 3,500 characters + 5 images with OCR.

Key insights:
1. Brand positioning: ...
2. Menu structure: ...
3. Differentiators: ..."

### Example 2: HFK Reference Material

**User:** "Analyze HFK AI team page: https://hfk.me/ai-team"

**Claude Actions:**
```bash
mkdir -p <PKM_ROOT>/10-projects/12-education/12.06-hfk-winter-ai

cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
python3 web-crawler.py \
    "https://hfk.me/ai-team" \
    <PKM_ROOT>/10-projects/12-education/12.06-hfk-winter-ai/hfk-ai-team-reference.md
```

### Example 3: Multiple URLs

**User:** "Analyze these 3 competitor sites:
- https://cafe-a.com
- https://cafe-b.com
- https://cafe-c.com"

**Claude:** Process each URL sequentially, then provide comparative analysis.

## Environment Setup

### Required Environment Variables

This skill requires two API keys:

```bash
export GEMINI_API_KEY="your_gemini_key_here"
export FIRECRAWL_API_KEY="your_firecrawl_key_here"
```

### Alternative: .env File

Create `.claude/skills/web-crawler-ocr/scripts/.env`:
```
GEMINI_API_KEY=your_gemini_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
```

Use `.env.example` as template:
```bash
cd .claude/skills/web-crawler-ocr/scripts
cp .env.example .env
# Edit .env with your actual API keys
```

### Check Setup

```bash
# Verify .env file
cat .claude/skills/web-crawler-ocr/scripts/.env

# Test script
cd .claude/skills/web-crawler-ocr/scripts && \
source venv/bin/activate && \
python3 web-crawler.py
```

## Limitations

- **Gemini Free Tier**: 15 requests per minute
- **Firecrawl Free Tier**: 500 credits
- **Image Limit**: Maximum 10 images per page
- **File Size**: 20MB per image maximum

## Troubleshooting

### API Key Errors

```bash
# Check if keys are set
echo $GEMINI_API_KEY
echo $FIRECRAWL_API_KEY

# Set if missing
export GEMINI_API_KEY="your_key"
export FIRECRAWL_API_KEY="your_key"
```

### Python Package Errors

```bash
cd .claude/skills/web-crawler-ocr/scripts
source venv/bin/activate
pip install -r requirements.txt
```

### Script Not Found

Verify script location:
```bash
ls -la .claude/skills/web-crawler-ocr/scripts/web-crawler.py
```

## Script Location

- **Main Script**: `.claude/skills/web-crawler-ocr/scripts/web-crawler.py`
- **Helper Script**: `.claude/skills/web-crawler-ocr/scripts/gemini-ocr.py`
- **Config Template**: `.claude/skills/web-crawler-ocr/scripts/.env.example`
- **Requirements**: `.claude/skills/web-crawler-ocr/scripts/requirements.txt`
- **Virtual Env**: `.claude/skills/web-crawler-ocr/scripts/venv/` (created on first run)

## Inspired By

Noah Brier's Claudesidian project:
- Firecrawl for web research
- Gemini for large image/PDF analysis
- Unix philosophy: simple composable tools

## Version History

- **v2.0.0 (2026-01-29)**: 외부 CDN 이미지 OCR 자동 처리
  - Firecrawl markdown에서 이미지 URL 추출 기능 추가
  - 외부 CDN 이미지 지원 (amc.apglobal.com 등)
  - 상품 상세 이미지 자동 필터링 (썸네일/아이콘 제외)
  - 이미지 크기 체크 (5KB 미만 자동 제외)
  - --max-images, --no-ocr 옵션 추가
  - tempfile.TemporaryDirectory 사용으로 임시파일 자동 정리

- **v1.3.0 (2025-01-17)**: venv 경량화 (203MB -> 54MB)
  - google-generativeai 패키지 제거 -> Gemini REST API 직접 호출
  - markdownify 패키지 제거 (미사용)
  - firecrawl-py 4.6.0 -> 4.13.0 업그레이드
  - 설치 시간 2분 -> 20초로 단축
  - 기능 동일, 의존성만 최적화

- **v1.2.0 (2025-11-28)**: OCR 재배치 로직 추가
  - Python: OCR 결과를 끝에 깔끔하게 추가 (간단 버전)
  - Skill: Step 5에 OCR 재배치 프로세스 추가 (필수)
  - Firecrawl v2 API 완전 지원 (Document 객체)
  - 2단계 워크플로우: 크롤링 → 재배치

- **v1.1.0 (2025-11-10)**: Skill 구조 정리 (공식 문서 원칙 준수)
  - 스크립트를 Skill 폴더 내로 이동
  - venv를 gitignore 처리 (requirements.txt만 유지)
  - 모든 경로를 `.claude/skills/web-crawler-ocr/scripts/`로 통일

- **v1.0.0 (2025-10-29)**: Initial skill creation
  - Firecrawl + Gemini OCR integration
  - Model-invoked automation
  - PKM-aware file organization
