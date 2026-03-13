# Do Better Workspace 분석 문서

> 작성일: 2025-12-29
> 용도: 워크스페이스 구조 및 기능 설명 (교육용)

## 1. 개요

**do-better-workspace**는 비개발자를 위한 AI 작업 환경으로, Claude Code와 Johnny Decimal 시스템을 결합한 실전 PKM(Personal Knowledge Management) 워크스페이스입니다.

**용도**: Claude Code + PKM 시스템 교육용으로 제작

**핵심 철학**:
1. AI amplifies thinking, not just writing
2. File system = AI memory
3. Structure enables creativity
4. Iteration over perfection
5. Immediate usability

---

## 2. 폴더 구조 (Johnny Decimal 시스템)

```
do-better-workspace/
├── .claude/              # Claude Code 확장 기능
│   ├── commands/         # 슬래시 커맨드 (13개)
│   ├── agents/           # 서브에이전트 (1개)
│   └── skills/           # 스킬스 (2개)
├── 00-inbox/             # 빠른 캡처 공간
├── 00-system/            # 시스템 설정 및 템플릿
│   ├── 01-templates/     # 재사용 템플릿 (4개)
│   ├── 02-scripts/       # 자동화 스크립트
│   ├── 03-guides/        # 가이드 문서
│   └── 04-docs/          # 문서
├── 10-projects/          # 활성 프로젝트 (시한부)
│   └── 11-consulting/    # 컨설팅 프레임워크
├── 20-operations/        # 비즈니스 운영 (지속적)
│   └── 21-hr/            # HR/노무 관련
├── 30-knowledge/         # 지식 아카이브
├── 40-personal/          # 개인 노트
│   ├── 41-daily/         # Daily Notes
│   ├── 42-weekly/        # Weekly Reviews
│   ├── 45-ideas/         # 아이디어
│   └── 46-todos/         # 할 일 관리
├── 50-resources/         # 참고 자료
└── 90-archive/           # 완료/중단 항목
```

---

## 3. Slash Commands

### 초기 설정
| 커맨드 | 설명 |
|--------|------|
| `/setup-workspace` | 대화형 CLAUDE.md 자동 생성 + 초기 설정 |

### Daily Workflow
| 커맨드 | 설명 |
|--------|------|
| `/daily-note` | 오늘 Daily Note 생성/열기 |
| `/daily-review` | 어제/오늘 변경사항 분석 |

### 지식 관리
| 커맨드 | 설명 |
|--------|------|
| `/idea [카테고리]` | 대화에서 아이디어 추출 후 PKM에 저장 |
| `/todo` | 할 일 추가 |
| `/todos [today/project/overdue/stats]` | 할 일 목록 조회/관리 |

### AI 활용
| 커맨드 | 설명 |
|--------|------|
| `/thinking-partner` | AI와 대화하며 생각 발전 (소크라테스식 질문) |

### 시스템
| 커맨드 | 설명 |
|--------|------|
| `/create-command` | 커스텀 명령어 생성 |

---

## 4. Skills (2개)

### 4.1 Notion Handler
**파일**: `.claude/skills/notion-handler/`

**기능**:
- Notion 데이터베이스/페이지 관리
- DB 생성, 페이지 추가

**트리거 키워드**: "노션", "Notion", "DB 만들어", "데이터베이스"

---

### 4.2 Transcript Organizer
**파일**: `.claude/skills/transcript-organizer/`

**기능**:
- 회의/강의 녹취록 정리
- 요점 추출 및 구조화

---

## 5. Agents (서브에이전트, 1개)

### 5.1 Zettelkasten Linker
**파일**: `.claude/agents/zettelkasten-linker.md`

**역할**: PKM vault 종합 분석 및 큐레이션

**기능**:
1. **Quality Assessment**: 파일 품질 평가 (삭제/분할/유지)
2. **Link Suggestion**: 양방향 연결 제안 (>60% 관련성)
3. **Vault Health Report**: 개선 계획 생성

---

## 6. Templates (4개)

| 템플릿 | 용도 |
|--------|------|
| `daily-note-template.md` | 매일 작성하는 노트 |
| `weekly-review-template.md` | 주간 회고 |
| `Project Template.md` | 새 프로젝트 시작 |
| `Daily Note Template.md` | (레거시) |

---

## 7. 샘플 데이터 (교육용)

`50-resources/sample-data/` 폴더에 **뉴믹스커피** 시나리오 기반의 교육용 데이터 포함

### 브랜드 설정
- **브랜드명**: 뉴믹스커피 (Newmix Coffee) by 그란데클립코리아
- **창업자**: 김봉진 의장 (배달의민족 창업자)
- **콘셉트**: 한국 믹스커피를 문화 콘텐츠로 재정의, 인바운드 관광객 기념품 포지셔닝
- **매장**: 성수점, 북촌점
- **상황**: 2026년 2월 마감, 3월 벚꽃 시즌 전략 미팅 준비

### 데이터셋 현황

| 파일명 | 설명 | 행 수 | 주요 컬럼 |
|--------|------|-------|-----------|
| `newmix_sales_seongsu_2602.csv` | 2월 성수 매장 매출 | 4,231 (1,957주문) | 날짜, 시간, 카테고리, 상품명, 수량, 단가, 합계, 결제수단, 고객국적 |
| `newmix_sales_seongsu_2601.csv` | 1월 성수 매장 매출 | 3,085 (1,534주문) | 동일 |
| `newmix_sales_bukchon_2602.csv` | 2월 북촌 매장 매출 | 3,139 (1,406주문) | 동일 |
| `newmix_online_sales_2602.csv` | 2월 온라인 매출 | 1,399 (814주문) | 주문일, 채널, 카테고리, 상품명, 수량, 단가, 합계, 배송지역, 주문상태 |
| `newmix_inventory_data.csv` | 전체 재고 현황 | 40품목 | 분류, 상품명, 발주처, 주차별판매, 총재고, 일판매량, 재고일수 |

### 실습 미션 (6개)

| 미션 | 데이터 | 분석 목표 |
|------|--------|-----------|
| 미션 1 | 성수 1월+2월 | 매출 현황 + 1월 대비 성장률, 주차별 추이, 베스트셀러 |
| 미션 2 | 성수 2월 | 고객 국적별 분석, 인바운드 전략 |
| 미션 3 | 재고 데이터 | 긴급 발주 품목, 벚꽃 시즌 대비 |
| 미션 4 | 성수+북촌 2월 | 매장간 고객층, 인기 상품, 객단가 비교 |
| 미션 5 | 온라인 2월 | 채널별(네이버/쿠팡/컬리) 매출, 지역별 수요 |
| 미션 6 | 전채널 5개 종합 | 봉진 의장 보고용 전채널 1페이지 요약 |

### 실습 가이드 위치
- **상세 가이드**: `00-system/claude-code-practice-guide.md`
- **데이터 설명**: `50-resources/sample-data/README.md`

---

## 8. 핵심 기능 연결도

```
┌─────────────────────────────────────────────────────────────┐
│                    INITIAL SETUP                            │
│  /setup-workspace -> 대화형 정보 수집 -> CLAUDE.md 자동 생성 │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW                           │
│  /daily-note -> Daily Note 생성                             │
│  /daily-review -> 변경사항 분석 -> 우선순위 제안             │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                AI 활용                                      │
│  /thinking-partner -> 소크라테스식 대화                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                KNOWLEDGE MANAGEMENT                         │
│  /idea -> 대화에서 인사이트 추출 -> 30-knowledge 저장        │
│  /todos -> 할 일 관리 -> active-todos.md                    │
│  Zettelkasten Linker -> 노트 연결 및 품질 관리              │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 사용자 시작 가이드

### 최초 설정 (5분)
```bash
# 1. Clone
git clone https://github.com/Rhim80/do-better-workspace.git
cd do-better-workspace

# 2. Claude Code에서 열기
# VS Code 또는 터미널에서 Claude Code 실행

# 3. 초기 설정 (대화형 CLAUDE.md 자동 생성)
/setup-workspace

```

### 매일 사용
```bash
/daily-note          # 아침: 오늘 계획
/todos today         # 오늘 할 일 확인
/daily-review        # 저녁: 하루 정리
```

### 생각 정리가 필요할 때
```bash
/thinking-partner    # 소크라테스식 대화
```

---

## 10. 기술 스택 요약

| 구성요소 | 기술 |
|----------|------|
| PKM 구조 | Johnny Decimal 시스템 |
| AI 에이전트 | Claude Code Subagents |
| 버전 관리 | Git |

---

## 11. Skills vs Commands vs Agents 비교

| 구분 | Skills | Commands | Agents |
|------|--------|----------|--------|
| **목적** | 외부 서비스 통합 | 내부 워크플로우 자동화 | 복잡한 다단계 작업 |
| **예시** | Web Crawler, Notion | `/daily-note`, `/todos` | Zettelkasten Linker |
| **위치** | `.claude/skills/` | `.claude/commands/` | `.claude/agents/` |
| **설정** | OAuth, API 키 필요 | 설정 불필요 (즉시 사용) | 설정 불필요 |
| **호출** | 키워드 자동 감지 | `/command` 형식 | 자연어 요청 |

---

## 12. 주요 특징 요약

1. **비개발자 친화적**: CLI 환경이지만 자연어로 대화하며 사용
2. **대화형 설정**: `/setup-workspace`로 CLAUDE.md 자동 생성
3. **체계적 구조**: Johnny Decimal로 AI가 이해하기 쉬운 폴더 구조
4. **AI 활용**: thinking-partner로 체계적 사고
5. **Daily Workflow 자동화**: Todo, 리뷰가 유기적으로 연결
6. **확장 가능**: Skills, Commands, Agents로 기능 확장 용이

---

**Made with Claude Code by hovoo (이림)**
F&B Professional x AI Practitioner
