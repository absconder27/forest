#!/usr/bin/env python3
"""
범용 웹 크롤러 + Gemini OCR 통합 시스템

Firecrawl로 텍스트 추출 → 이미지 다운로드 → Gemini OCR → 완전한 마크다운 생성

사용법:
  python web-crawler.py <URL> [출력_파일명]

예시:
  python web-crawler.py https://example.com/article
  python web-crawler.py https://competitor-cafe.com analysis.md

v2.0.0 (2026-01-29): 외부 CDN 이미지 OCR 자동 처리
  - Firecrawl markdown에서 이미지 URL 추출 기능 추가
  - 외부 CDN 이미지 지원 (amc.apglobal.com 등)
  - 상품 상세 이미지 필터링 (썸네일, 아이콘 제외)
  - 이미지 크기 체크 (5KB 미만 제외)
"""

import os
import sys
import re
import requests
import base64
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# 색상 출력
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_color(text, color):
    """색상 출력"""
    print(f"{color}{text}{Colors.NC}")

def check_api_keys():
    """API 키 확인"""
    missing = []

    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if not FIRECRAWL_API_KEY:
        missing.append("FIRECRAWL_API_KEY")

    if missing:
        print_color(f"Missing API keys: {', '.join(missing)}", Colors.RED)
        print("\n설정 방법:")
        print("1. .env 파일 생성 또는 환경변수 설정:")
        print("   GEMINI_API_KEY='your_key_here'")
        print("   FIRECRAWL_API_KEY='your_key_here'")
        print("\n2. API 키 발급:")
        print("   - Gemini: https://aistudio.google.com/apikey")
        print("   - Firecrawl: https://firecrawl.dev")
        sys.exit(1)


def extract_images_from_markdown(markdown_content, base_url):
    """Firecrawl markdown에서 이미지 URL 추출 (v2.0 추가)"""
    # 마크다운 이미지 패턴: ![alt](url) 또는 [![alt](url)](link)
    patterns = [
        r'!\[([^\]]*)\]\(([^)\s]+)',  # ![alt](url)
        r'\[!\[([^\]]*)\]\(([^)\s]+)',  # [![alt](url)]
    ]

    image_urls = []
    seen = set()

    for pattern in patterns:
        matches = re.findall(pattern, markdown_content)
        for match in matches:
            alt = match[0] if match[0] else ''
            url = match[1]

            # URL 정리 - 쿼리 파라미터 유지 (content-disposition 등)
            url = url.rstrip(')')

            # 상대 URL을 절대 URL로 변환
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)

            if url not in seen:
                seen.add(url)
                image_urls.append({'url': url, 'alt': alt})

    return image_urls


def filter_product_images(image_list, max_images=15):
    """상품 상세 이미지만 필터링 - 썸네일/아이콘 제외 (v2.0 추가)"""
    filtered = []

    # 제외할 패턴 (URL에서 확인)
    exclude_patterns = [
        'thumbnail', 'thumb', 'icon', 'logo', 'banner',
        'btn', 'button', 'arrow', 'close', 'search',
        'profile', 'avatar', 'emoji', 'spinner', 'loading',
        'RS=64', 'RS=32', 'RS=48', 'RS=100',  # 작은 리사이즈 이미지
        'reviewProfile', 'user_profile',
    ]

    # 포함 우선 패턴 (상품 상세 이미지 특징)
    priority_patterns = [
        'apglobal.com', 'asset/', 'goods/', 'product/',
        'detail', 'content', 'description', 'inline',
    ]

    priority_images = []
    normal_images = []

    for img in image_list:
        url = img['url']
        url_lower = url.lower()

        # 제외 패턴 체크
        if any(exc in url_lower for exc in exclude_patterns):
            continue

        # GIF 제외 (애니메이션)
        if url_lower.endswith('.gif') or '.gif?' in url_lower:
            continue

        # 포함 패턴이 있으면 우선 리스트에 추가
        if any(inc in url_lower for inc in priority_patterns):
            priority_images.append(img)
        else:
            normal_images.append(img)

    # 우선 이미지 먼저, 나머지 이미지 뒤에
    filtered = priority_images + normal_images

    return filtered[:max_images]

def crawl_with_firecrawl(url, wait_for=None, timeout=30000, scroll=False):
    """Firecrawl로 웹페이지 크롤링 (동적 콘텐츠 지원)

    Args:
        url: 크롤링할 URL
        wait_for: JS 렌더링 대기 시간 (ms), 기본값 None
        timeout: 전체 타임아웃 (ms), 기본값 30000
        scroll: 무한 스크롤 페이지 여부, 기본값 False
    """
    print_color(f"🔍 Firecrawl로 텍스트 추출 중: {url}", Colors.BLUE)

    try:
        from firecrawl import Firecrawl

        firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)

        # 스크래핑 옵션 구성
        scrape_options = {
            'formats': ['markdown', 'html'],
            'timeout': timeout,
        }

        # 동적 콘텐츠 대기 옵션
        if wait_for:
            scrape_options['waitFor'] = wait_for
            print_color(f"⏳ JS 렌더링 대기: {wait_for}ms", Colors.BLUE)

        # 무한 스크롤 처리
        if scroll:
            scrape_options['actions'] = [
                {"type": "scroll", "direction": "down", "amount": 3}
            ]
            print_color("📜 스크롤 액션 활성화", Colors.BLUE)

        doc = firecrawl.scrape(url, **scrape_options)

        # v2 API는 Document 객체를 반환
        if doc:
            markdown = doc.markdown if hasattr(doc, 'markdown') else ''
            html = doc.html if hasattr(doc, 'html') else ''
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}

            print_color(f"✅ 텍스트 추출 완료 ({len(markdown)} 글자)", Colors.GREEN)
            return {
                'markdown': markdown,
                'html': html,
                'metadata': metadata
            }
        else:
            print_color("⚠️ Firecrawl 실패, BeautifulSoup으로 대체", Colors.YELLOW)
            return crawl_with_beautifulsoup(url)

    except ImportError:
        print_color("⚠️ firecrawl-py 미설치, BeautifulSoup으로 대체", Colors.YELLOW)
        return crawl_with_beautifulsoup(url)
    except Exception as e:
        print_color(f"⚠️ Firecrawl 오류: {e}, BeautifulSoup으로 대체", Colors.YELLOW)
        return crawl_with_beautifulsoup(url)

def crawl_with_beautifulsoup(url):
    """BeautifulSoup으로 대체 크롤링"""
    print_color("🔄 BeautifulSoup으로 크롤링 중...", Colors.BLUE)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # 본문 추출
    article = soup.find('article') or soup.find('main') or soup.body
    text = article.get_text(separator='\n', strip=True) if article else soup.get_text(separator='\n', strip=True)

    # 메타데이터 추출
    title = soup.find('title')
    title_text = title.text if title else urlparse(url).netloc

    return {
        'markdown': text,
        'html': str(soup),
        'metadata': {
            'title': title_text,
            'sourceURL': url
        }
    }


def download_image(url, output_dir, min_size_kb=5):
    """이미지 다운로드 (v2.0 개선: 크기 체크, 해시 파일명)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # 컨텐츠 타입에서 확장자 결정
        content_type = response.headers.get('content-type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            # URL에서 확장자 추출
            path_ext = Path(urlparse(url).path).suffix.lower()
            ext = path_ext if path_ext in ['.jpg', '.jpeg', '.png', '.webp'] else '.jpg'

        # 파일명 생성 (URL 해시로 중복 방지)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"img_{url_hash}{ext}"
        filepath = output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(response.content)

        # 이미지 크기 확인 (너무 작으면 아이콘일 가능성)
        file_size_kb = filepath.stat().st_size / 1024
        if file_size_kb < min_size_kb:
            print_color(f"  Skip (too small: {file_size_kb:.1f}KB): {url[:50]}...", Colors.YELLOW)
            filepath.unlink()
            return None

        return filepath
    except Exception as e:
        print_color(f"  Download failed: {url[:50]}... ({e})", Colors.YELLOW)
        return None

def analyze_image_with_gemini(image_path):
    """Gemini REST API로 이미지 OCR 및 분석 (경량화)"""
    try:
        # 이미지를 base64로 인코딩
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()

        # 이미지 MIME 타입 결정
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        # REST API 호출
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [
                        {"text": "이 이미지의 모든 텍스트를 추출하고, 주요 내용을 설명해주세요. 한글로 답변해주세요."},
                        {"inline_data": {"mime_type": mime_type, "data": image_data}}
                    ]
                }]
            },
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"API 오류: {response.status_code}")

        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print_color(f"⚠️ Gemini 분석 실패: {e}", Colors.YELLOW)
        return None

def process_url(url, output_file=None, wait_for=None, scroll=False, max_images=15):
    """URL 전체 처리 워크플로우 (v2.0 개선)

    Args:
        url: 크롤링할 URL
        output_file: 출력 파일 경로
        wait_for: JS 렌더링 대기 시간 (ms)
        scroll: 무한 스크롤 페이지 여부
        max_images: 최대 OCR 처리할 이미지 수 (기본: 15)
    """

    print_color(f"\n{'='*80}", Colors.BLUE)
    print_color(f"Web Crawler + OCR v2.0", Colors.BLUE)
    print_color(f"{'='*80}\n", Colors.BLUE)

    # 1. Firecrawl로 텍스트 크롤링 (동적 옵션 전달)
    crawl_result = crawl_with_firecrawl(url, wait_for=wait_for, scroll=scroll)
    markdown_text = crawl_result['markdown']
    html = crawl_result['html']
    metadata = crawl_result['metadata']

    # 2. 이미지 URL 추출 (v2.0: HTML + Markdown 양쪽에서 추출)
    all_images = []
    seen_urls = set()

    # 2-1. Firecrawl markdown에서 이미지 추출 (v2.0 추가 - 외부 CDN 이미지 포함)
    md_images = extract_images_from_markdown(markdown_text, url)
    for img in md_images:
        if img['url'] not in seen_urls:
            seen_urls.add(img['url'])
            all_images.append(img)

    print_color(f"Markdown에서 {len(md_images)}개 이미지 발견", Colors.CYAN)

    # 2-2. HTML에서 이미지 추출
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('article') or soup.find('main') or soup.body

    html_image_count = 0
    if content:
        for img_tag in content.find_all('img'):
            src = img_tag.get('src') or img_tag.get('data-src')
            if src:
                full_url = urljoin(url, src)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    alt = img_tag.get('alt', '')
                    all_images.append({'url': full_url, 'alt': alt})
                    html_image_count += 1

    print_color(f"HTML에서 {html_image_count}개 추가 이미지 발견", Colors.CYAN)
    print_color(f"총 {len(all_images)}개 이미지 발견", Colors.GREEN)

    # 3. 상품 상세 이미지 필터링 (v2.0: 썸네일/아이콘 제외)
    filtered_images = filter_product_images(all_images, max_images=max_images)
    print_color(f"필터링 후 {len(filtered_images)}개 이미지 OCR 대상", Colors.GREEN)

    # 4. 이미지 다운로드 및 OCR (v2.0: tempfile 사용)
    image_ocr_list = []

    if filtered_images:
        print_color(f"\nGemini OCR 처리 중...", Colors.BLUE)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for i, img in enumerate(filtered_images, 1):
                print_color(f"  [{i}/{len(filtered_images)}] {img['url'][:60]}...", Colors.NC)

                # 다운로드
                filepath = download_image(img['url'], temp_path)
                if not filepath:
                    continue

                # Gemini OCR
                analysis = analyze_image_with_gemini(filepath)
                if analysis:
                    image_ocr_list.append({
                        'url': img['url'],
                        'alt': img.get('alt', ''),
                        'analysis': analysis
                    })
                    print_color(f"    OCR: {len(analysis)} chars extracted", Colors.GREEN)

    # 4. 최종 마크다운 생성 (Firecrawl markdown + 이미지 OCR 끝에 추가)
    final_markdown = generate_markdown_simple(
        url=url,
        metadata=metadata,
        markdown_text=markdown_text,
        image_ocr_list=image_ocr_list
    )

    # 5. 파일 저장
    if not output_file:
        # URL에서 파일명 생성
        domain = urlparse(url).netloc.replace('www.', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{domain}_{timestamp}.md"

    output_path = Path(output_file)
    output_path.write_text(final_markdown, encoding='utf-8')

    print_color(f"\n{'='*80}", Colors.GREEN)
    print_color(f"✅ 완료: {output_path.absolute()}", Colors.GREEN)
    print_color(f"{'='*80}\n", Colors.GREEN)

    return output_path

def generate_markdown_simple(url, metadata, markdown_text, image_ocr_list):
    """Firecrawl markdown + 모든 OCR 결과를 끝에 추가 (간단 버전)"""

    # metadata는 dict 또는 Pydantic 객체일 수 있음
    if isinstance(metadata, dict):
        title = metadata.get('title', 'Untitled')
    else:
        title = getattr(metadata, 'title', 'Untitled')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 헤더 생성
    md = f"""# {title}

> 출처: {url}
> 크롤링: {timestamp}
> 도구: Firecrawl + Gemini OCR

---

"""

    # Firecrawl markdown 추가
    md += markdown_text
    md += "\n\n"

    # 모든 이미지 OCR 결과를 끝에 추가
    if image_ocr_list:
        md += "---\n\n"
        md += "## 📸 이미지 OCR 결과\n\n"
        md += "> 아래는 Gemini가 추출한 이미지 내용입니다.\n"
        md += "> 각 이미지의 내용을 확인하고, 위 본문의 적절한 위치로 이동시킬 수 있습니다.\n\n"

        for i, img_data in enumerate(image_ocr_list, 1):
            md += f"### 이미지 {i}\n\n"
            if img_data.get('alt'):
                md += f"**ALT 텍스트**: {img_data['alt']}\n\n"
            md += f"**이미지 URL**: `{img_data['url']}`\n\n"
            md += "**OCR 추출 내용**:\n\n"
            md += "```\n"
            md += img_data['analysis']
            md += "\n```\n\n"
            md += "---\n\n"

    return md

def generate_markdown_with_inline_images(url, metadata, markdown_text, html, image_ocr_list):
    """Firecrawl markdown에 이미지 OCR 내용을 HTML 순서대로 삽입"""

    # metadata는 dict 또는 Pydantic 객체일 수 있음
    if isinstance(metadata, dict):
        title = metadata.get('title', 'Untitled')
    else:
        title = getattr(metadata, 'title', 'Untitled')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 헤더 생성
    md = f"""# {title}

> 출처: {url}
> 크롤링: {timestamp}
> 도구: Firecrawl + Gemini OCR

---

"""

    if not image_ocr_list:
        # 이미지가 없으면 Firecrawl markdown 그대로 반환
        md += markdown_text
        return md

    # HTML에서 이미지와 텍스트 노드의 상대적 위치 파악
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('article') or soup.find('main') or soup.body

    if not content:
        md += markdown_text
        return md

    # HTML에서 텍스트 청크와 이미지의 순서 추출
    structure = []

    for element in content.descendants:
        if element.name == 'img':
            src = element.get('src') or element.get('data-src')
            if src:
                full_url = urljoin(url, src)
                # 이미지 OCR 리스트에서 매칭
                for ocr in image_ocr_list:
                    if ocr['url'] == full_url:
                        structure.append({
                            'type': 'image',
                            'data': ocr
                        })
                        break

        elif element.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']:
            text = element.get_text(strip=True)
            if text and len(text) > 20:  # 의미 있는 텍스트만
                structure.append({
                    'type': 'text_marker',
                    'text': text[:50]  # 첫 50자만 저장 (마커용)
                })

    # Firecrawl markdown을 줄 단위로 분할
    markdown_lines = markdown_text.split('\n')

    # 구조 정보를 바탕으로 이미지 삽입 위치 찾기
    result_lines = []
    image_idx = 0
    text_marker_idx = 0

    for line in markdown_lines:
        result_lines.append(line)

        # 현재 줄에 structure의 text_marker가 있는지 확인
        if text_marker_idx < len(structure):
            item = structure[text_marker_idx]

            if item['type'] == 'text_marker':
                # 현재 줄이 마커 텍스트를 포함하는지 확인
                if item['text'][:30] in line:
                    text_marker_idx += 1

                    # 다음 항목이 이미지인지 확인
                    if text_marker_idx < len(structure) and structure[text_marker_idx]['type'] == 'image':
                        img_data = structure[text_marker_idx]['data']

                        # 이미지 OCR 블록 삽입
                        result_lines.append("")
                        result_lines.append("---")
                        result_lines.append("")

                        if img_data['alt']:
                            result_lines.append(f"**[이미지: {img_data['alt']}]**")
                        else:
                            result_lines.append("**[이미지]**")

                        result_lines.append("")
                        result_lines.append("```")
                        result_lines.append(img_data['analysis'])
                        result_lines.append("```")
                        result_lines.append("")
                        result_lines.append("---")
                        result_lines.append("")

                        text_marker_idx += 1

    md += '\n'.join(result_lines)
    return md

def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(
        description='웹 크롤러 + Gemini OCR (동적 콘텐츠 지원)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 크롤링
  python web-crawler.py https://example.com/article

  # 출력 파일 지정
  python web-crawler.py https://example.com output.md

  # 동적 페이지 (JS 렌더링 대기 3초)
  python web-crawler.py https://spa-site.com --wait 3000

  # 무한 스크롤 페이지
  python web-crawler.py https://infinite-scroll.com --scroll

  # 동적 + 스크롤 + 출력 파일
  python web-crawler.py https://complex-site.com result.md --wait 2000 --scroll
        """
    )

    parser.add_argument('url', help='크롤링할 URL')
    parser.add_argument('output', nargs='?', help='출력 파일 경로 (선택)')
    parser.add_argument('--wait', type=int, help='JS 렌더링 대기 시간 (ms), 예: --wait 3000')
    parser.add_argument('--scroll', action='store_true', help='무한 스크롤 페이지 처리')
    parser.add_argument('--max-images', type=int, default=15, help='최대 OCR 처리 이미지 수 (기본: 15)')
    parser.add_argument('--no-ocr', action='store_true', help='OCR 처리 건너뛰기')

    # API 키 확인
    check_api_keys()

    args = parser.parse_args()

    # 처리 실행
    result = process_url(
        url=args.url,
        output_file=args.output,
        wait_for=args.wait,
        scroll=args.scroll,
        max_images=0 if args.no_ocr else args.max_images
    )

    print(f"📂 결과 파일: {result}")
    print("\n💡 Claude Code에서 활용:")
    print(f"   > {result} 읽고 핵심 인사이트 정리해줘")

if __name__ == "__main__":
    main()
