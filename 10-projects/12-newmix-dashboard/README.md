# 12 뉴믹스 마케팅 대시보드

국가별(일본/대만/중국) 마케팅 예산 배분을 데이터 기반으로 결정하기 위한 웹 대시보드 프로젝트

## 프로젝트 정보

| 항목 | 내용 |
|------|------|
| **상태** | Phase 1 (MVP) 개발 중 |
| **시작일** | 2026-03-15 |
| **사용자** | 뉴믹스 마케팅팀 |
| **기술 스택** | Streamlit, Plotly, Gmail API |
| **대시보드 실행** | `streamlit run dashboard/app.py` |

## 문서

- [PRD (제품 요구사항)](docs/prd.md) - 제품 기획, KPI, 로드맵
- [디자인 가이드](docs/design-guide.md) - 스타일가이드, 컬러 팔레트, 컴포넌트

## 구현 파일

| 파일 | 역할 |
|------|------|
| `dashboard/app.py` | Streamlit 메인 앱 |
| `dashboard/charts.py` | Plotly 차트 컴포넌트 |
| `dashboard/data_fetcher.py` | Gmail 매출 데이터 파싱 |

## 로드맵

- [x] **Phase 1**: 국가별 매출 현황 대시보드 (MVP)
- [ ] **Phase 2**: 콘텐츠 트래커 (SNS 포스팅 입력/관리)
- [ ] **Phase 3**: 콘텐츠-매출 상관관계 분석
