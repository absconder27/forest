# Claude Code Skills - Source of Truth

> **Source**: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills), [platform.claude.com Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
> **Updated**: 2026-02-22
> **Purpose**: Skills 개발 시 유일한 참조 문서. 이 파일이 source of truth.

---

## 1. Skills 개요

**Skills**는 Claude Code의 기능을 확장하는 모듈형 컴포넌트. `SKILL.md` 파일 하나로 Claude가 새로운 능력을 갖추게 됨.

### 핵심 특성

- Claude가 **자동으로 판단하여 실행** (model-invoked)
- 사용자가 `/skill-name`으로 **직접 호출**도 가능 (user-invoked)
- 스크립트 번들링으로 **결정론적 코드** 실행 가능
- [Agent Skills](https://agentskills.io) 오픈 스탠다드 준수

### Slash Commands와의 관계

- `.claude/commands/review.md`와 `.claude/skills/review/SKILL.md`는 동일하게 `/review` 생성
- 기존 `.claude/commands/` 파일은 계속 작동
- **같은 이름일 경우 Skill이 우선**
- Skills가 상위 호환: 지원 파일 디렉토리, frontmatter 호출 제어, 자동 로드

---

## 2. 파일 구조

### 기본 구조

```
my-skill/
├── SKILL.md           # 메인 인스트럭션 (필수, 유일한 필수 파일)
├── reference.md       # 상세 API 문서 (필요 시 로드)
├── examples.md        # 사용 예시 (필요 시 로드)
└── scripts/
    └── helper.py      # 유틸리티 스크립트 (실행만, 컨텍스트에 로드 안 됨)
```

### Skill 저장 위치

| 위치 | 경로 | 적용 범위 |
|------|------|----------|
| Enterprise | 관리 설정 참조 | 조직의 모든 사용자 |
| Personal | `~/.claude/skills/<name>/SKILL.md` | 모든 프로젝트 |
| Project | `.claude/skills/<name>/SKILL.md` | 해당 프로젝트만 |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | 플러그인 활성화된 곳 |

**우선순위**: enterprise > personal > project
동일 이름 시 높은 우선순위가 승리. Plugin은 `plugin-name:skill-name` 네임스페이스로 충돌 없음.

### 자동 발견

- 중첩 디렉토리: `packages/frontend/` 편집 시 `packages/frontend/.claude/skills/`도 탐색 (모노레포 지원)
- `--add-dir`로 추가된 디렉토리의 `.claude/skills/`도 자동 로드
- 라이브 변경 감지: 세션 재시작 없이 SKILL.md 편집 즉시 반영

---

## 3. YAML Frontmatter 전체 필드

```yaml
---
name: my-skill
description: What this skill does and when to use it
argument-hint: [issue-number]
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Grep, Glob
model: sonnet
context: fork
agent: Explore
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check.sh"
---
```

### 필드 상세

| 필드 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `name` | 권장 | 디렉토리명 | 소문자, 숫자, 하이픈만. 최대 64자. "anthropic", "claude" 예약어 금지. XML 태그 금지. |
| `description` | 권장 | 마크다운 첫 단락 | Claude가 언제 사용할지 판단 기준. **최대 1024자**. XML 태그 금지. |
| `argument-hint` | - | 없음 | 자동완성 시 보이는 힌트. 예: `[issue-number]`, `[filename] [format]` |
| `disable-model-invocation` | - | `false` | `true`: Claude 자동 실행 차단. `/name`으로만 호출 가능. |
| `user-invocable` | - | `true` | `false`: `/` 메뉴에서 숨김. Claude는 여전히 자동 호출 가능. 배경 지식 스킬용. |
| `allowed-tools` | - | 전체 | 스킬 활성 시 권한 요청 없이 사용 가능한 툴들. 쉼표 구분. |
| `model` | - | 상속 | 스킬 활성 시 사용할 모델. `sonnet`, `opus`, `haiku` |
| `context` | - | 인라인 | `fork`: 분기된 서브에이전트 컨텍스트에서 실행 |
| `agent` | - | `general-purpose` | `context: fork` 시 사용할 에이전트. 내장: `Explore`, `Plan`, `general-purpose`. 커스텀: `.claude/agents/`의 에이전트. |
| `hooks` | - | 없음 | 스킬 라이프사이클 범위의 훅. 스킬 종료 시 자동 정리. |

### 호출 제어 매트릭스

| Frontmatter | 사용자 호출 | Claude 호출 | 설명 로드 |
|-------------|------------|------------|----------|
| (기본값) | O | O | 설명 항상 컨텍스트에 |
| `disable-model-invocation: true` | O | X | 설명이 컨텍스트에 없음 |
| `user-invocable: false` | X | O | 설명 항상 컨텍스트에 |

---

## 4. 3단계 로딩 메커니즘

Skills는 토큰 효율을 위해 3단계로 로딩됨.

### Level 1: Metadata (항상 로드)
- YAML frontmatter의 `name`과 `description`
- 세션 시작 시 시스템 프롬프트에 포함
- 스킬당 약 100 토큰

### Level 2: Instructions (트리거 시 로드)
- `SKILL.md`의 메인 바디
- 관련 요청이 있을 때만 로드
- **5,000 토큰 미만 권장**

### Level 3: Resources (필요 시 로드)
- 번들된 지원 파일 (reference.md, examples.md 등)
- 스크립트는 실행만 되고 컨텍스트에 로드 안 됨
- 실질적 제한 없음

### SKILL.md에서 지원 파일 참조

```markdown
## Additional resources
- For complete API details, see [reference.md](reference.md)
- For usage examples, see [examples.md](examples.md)
```

**SKILL.md는 500줄 미만 유지 권장.**

---

## 5. Context Budget

- 스킬 설명 로딩 예산: **컨텍스트 윈도우의 2%**, fallback 16,000자
- 스킬이 많으면 예산 초과 가능
- `/context`로 제외된 스킬 경고 확인
- `SLASH_COMMAND_TOOL_CHAR_BUDGET` 환경 변수로 재정의 가능

---

## 6. String Substitutions

SKILL.md 콘텐츠 내에서 사용 가능한 변수들.

| 변수 | 설명 |
|------|------|
| `$ARGUMENTS` | 스킬 호출 시 전달된 모든 인자. 콘텐츠에 없으면 `ARGUMENTS: <value>`로 끝에 자동 추가. |
| `$ARGUMENTS[N]` | 0-based 인덱스로 특정 인자 접근. 예: `$ARGUMENTS[0]` = 첫 번째 인자 |
| `$N` | `$ARGUMENTS[N]`의 단축형. `$0` = 첫 번째, `$1` = 두 번째 |
| `${CLAUDE_SESSION_ID}` | 현재 세션 ID. 로깅, 세션별 파일 생성에 유용. |

### 사용 예시

```markdown
---
name: review-pr
description: Review a pull request
argument-hint: [pr-number]
---

Review pull request #$0:
1. Fetch PR diff
2. Analyze changes
3. Provide feedback
```

---

## 7. Dynamic Context Injection

`!`command`` 문법으로 셸 커맨드를 실행하고 결과를 주입.

```markdown
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`
```

**동작 방식**:
- 스킬 콘텐츠가 Claude에게 전송되기 **전에** 실행
- 커맨드 출력이 플레이스홀더를 대체
- Claude는 전처리된 최종 결과만 봄

---

## 8. Subagent 실행 (context: fork)

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**동작**:
- `context: fork`: 격리된 컨텍스트에서 실행. 대화 히스토리 접근 불가.
- 결과는 메인 대화로 반환
- `agent` 생략 시 `general-purpose` 사용

**주의**: `context: fork`는 명시적 인스트럭션이 있는 스킬에서만 의미 있음. 가이드라인만 있는 스킬은 동작 없이 반환됨.

---

## 9. Subagents에 Skills 프리로드

서브에이전트에서 스킬을 사용하려면 명시적으로 `skills` 필드를 지정해야 함.

```yaml
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---

Implement API endpoints. Follow the conventions and patterns from the preloaded skills.
```

- `skills` 필드: 서브에이전트 시작 시 전체 스킬 콘텐츠를 컨텍스트에 주입
- 호출용이 아닌 직접 주입
- 서브에이전트는 부모 대화에서 스킬을 **상속받지 않음**

---

## 10. Hooks

스킬 라이프사이클 범위의 훅. 스킬 활성 시에만 실행, 종료 시 자동 정리.

```yaml
---
name: secure-operations
description: Perform operations with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
          once: true
---
```

| 이벤트 | 실행 시점 |
|--------|----------|
| PreToolUse | 도구 실행 전 |
| PostToolUse | 도구 실행 후 |
| Stop | 스킬 종료 시 (SubagentStop으로 자동 변환) |

**옵션**:
- `matcher`: 특정 도구 이름과 매칭 (예: `"Bash"`, `"*"`)
- `once: true`: 세션에서 한 번만 실행 (스킬 전용, 에이전트에서는 미지원)

---

## 11. Extended Thinking

스킬 콘텐츠 어디서든 **"ultrathink"** 단어를 포함하면 확장 사고(extended thinking) 모드가 활성화됨.

---

## 12. Skill Permission Control

### 모든 스킬 비활성화
```
# /permissions deny 규칙에 추가:
Skill
```

### 특정 스킬 허용/차단
```
# 특정 스킬만 허용
Skill(commit)
Skill(review-pr *)

# 특정 스킬 차단 (deny에 추가)
Skill(deploy *)
```

**문법**:
- `Skill(name)`: 정확한 이름 매치
- `Skill(name *)`: 접두사 매치 (인자 포함)

`user-invocable`은 메뉴 표시만 제어. 프로그래밍 방식 호출 차단은 `disable-model-invocation: true` 사용.

---

## 13. Description 작성 Best Practice

Description은 **가장 중요한 필드**. Claude가 언제 스킬을 사용할지 결정하는 유일한 기준 (body는 트리거 후에만 로드).

### 필수 규칙

1. **3인칭으로 작성** (시스템 프롬프트에 주입되므로)
   - Good: `Processes Excel files and generates reports`
   - Bad: `I can help you process Excel files`
   - Bad: `You can use this to process Excel files`

2. **무엇 + 언제** 둘 다 포함
   - 무엇을 하는지 + 언제 사용해야 하는지

3. **트리거 키워드 포함**
   - 사용자가 자연스럽게 말할 표현을 description에 포함
   - 한국어 스킬이면 한국어 키워드 필수

4. **1024자 이내**

5. **"When to Use" 정보는 description에**
   - body에 "When to Use This Skill" 섹션을 넣어도 트리거 판단에 도움 안 됨
   - description에 있어야 Claude가 판단 가능

### 좋은 예시

```yaml
description: Google Calendar 일정 조회, 검색, 등록. "오늘 일정", "이번 주 일정", "일정 검색", "미팅 잡아줘" 등을 언급하면 자동 실행.
```

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

### 나쁜 예시

```yaml
description: Helps with documents  # 너무 모호
description: Calendar management    # 키워드 부족
description: A useful tool          # 정보 없음
```

---

## 14. Naming Conventions

### 규칙

- **소문자, 숫자, 하이픈만** 허용
- 최대 64자
- "anthropic", "claude" 포함 금지 (예약어)
- XML 태그 금지

### 권장 형식

- Gerund: `processing-pdfs`, `analyzing-spreadsheets`
- 명사구: `pdf-processing`, `spreadsheet-analysis`
- 액션: `process-pdfs`, `analyze-spreadsheets`

### 피해야 할 이름

`helper`, `utils`, `tools`, `documents`, `data`, `files` (너무 모호)

---

## 15. Skill Content Types

### Reference Content (참조형)

Claude가 현재 작업에 적용하는 지식. 인라인 실행 (대화 컨텍스트와 함께 사용).

```yaml
---
name: api-conventions
description: API design patterns and conventions for this codebase. Loaded when writing API endpoints.
---

When writing API endpoints:
- Use RESTful naming conventions
- Return consistent error formats
- Include request validation
```

적합한 경우: 컨벤션, 패턴, 스타일 가이드, 도메인 지식

### Task Content (작업형)

단계별 인스트럭션. 직접 호출이 적합.

```yaml
---
name: deploy
description: Deploy the application to production
context: fork
disable-model-invocation: true
---

Deploy the application:
1. Run the test suite
2. Build the application
3. Push to the deployment target
```

적합한 경우: 배포, 데이터 처리, 복잡한 워크플로우

---

## 16. allowed-tools 사용법

### 기본

```yaml
allowed-tools: Read, Grep, Glob
```

### Bash 제한

```yaml
allowed-tools: Bash(gh *), Read
```

`Bash(gh *)`: `gh`로 시작하는 명령만 허용

### 사용 가능한 주요 도구

`Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `WebFetch`, `WebSearch`, `Task`, `Skill`, `NotebookEdit`

MCP 도구: `mcp__server-name__tool-name` 형식

---

## 17. @file 참조 및 !command 문법 (콘텐츠 내)

Skills/Commands 콘텐츠에서 사용 가능한 전처리 문법들.

### @file 참조

```markdown
Review these configuration files:

@package.json
@tsconfig.json
@.eslintrc.js
```

`@` 접두사가 붙은 파일 내용이 프롬프트에 포함됨.

### !command 실행

```markdown
Recent changes:
!git log --oneline -5
!git diff HEAD~1
```

`!` 접두사가 붙은 명령어 출력이 프롬프트에 포함됨. 스킬 콘텐츠가 Claude에게 전송되기 전에 실행.

### Plugin/MCP 네임스페이스

- **Plugin Commands**: `/plugin-name:command-name` (충돌 없으면 접두사 생략 가능)
- **MCP Slash Commands**: `/mcp__<server-name>__<prompt-name>` (MCP 서버 연결 시 자동 생성)

---

## 18. Troubleshooting

### 스킬이 트리거되지 않음

1. description에 사용자가 말할 키워드 포함 여부 확인
2. `What skills are available?`로 존재 확인
3. `/skill-name`으로 직접 호출하여 스킬 자체 동작 확인
4. description을 더 구체적으로 수정

### 스킬이 너무 자주 트리거됨

1. description을 더 좁게 수정
2. `disable-model-invocation: true` 추가

### Claude가 모든 스킬을 보지 못함

- 스킬이 너무 많으면 context budget 초과
- `/context`로 제외된 스킬 경고 확인
- `SLASH_COMMAND_TOOL_CHAR_BUDGET` 환경 변수로 한도 조정

### 파일 경로 확인

- YAML `---`가 반드시 1번째 줄 (앞에 빈 줄 없음)
- frontmatter와 내용 사이에 `---`로 구분
- 들여쓰기에 탭이 아닌 스페이스

---

## 19. Skills vs 다른 옵션

| 방법 | 목적 | 실행 시점 |
|------|------|----------|
| **Skills** | 전문 지식/기능 추가 | Claude 자동 판단 + 사용자 호출 |
| **Slash Commands** | 재사용 프롬프트 | `/command` 입력 시 |
| **CLAUDE.md** | 프로젝트 전체 지침 | 모든 대화에 항상 로드 |
| **Subagents** | 별도 컨텍스트 위임 | Claude 위임 또는 직접 호출 |
| **Hooks** | 이벤트 기반 스크립트 | 특정 도구 이벤트 시 |
| **MCP** | 외부 도구/데이터 연결 | Claude 필요시 호출 |

---

## 20. Best Practice Checklist

### DO

- [ ] description에 트리거 키워드 포함 (사용자가 실제로 말할 표현)
- [ ] description을 3인칭으로 작성
- [ ] SKILL.md 500줄, 5k 토큰 미만 유지
- [ ] 상세 문서는 지원 파일로 분리 (progressive disclosure)
- [ ] 스크립트를 번들링하여 결정론적 실행 활용
- [ ] 민감한 작업에 `disable-model-invocation: true` 설정
- [ ] `allowed-tools`로 최소 권한 원칙 적용
- [ ] 배포 전 트리거 테스트

### DON'T

- [ ] 모호한 description 사용 (helper, utils, tools)
- [ ] body에 "When to Use" 섹션만 두고 description 비움
- [ ] 모든 문서를 SKILL.md 한 파일에 몰아넣음
- [ ] "anthropic", "claude" 이름 사용
- [ ] 깊게 중첩된 파일 참조 (A -> B -> C)
- [ ] 외부 패키지 의존성 미언급

---

## 21. Practical Template

새 스킬 생성 시 시작점.

```yaml
---
name: skill-name
description: [3인칭] [무엇을 하는지] [언제 사용하는지 + 트리거 키워드]
allowed-tools: [최소 필요 도구]
---

# [Skill Name]

## Overview
[한 문단: 이 스킬이 하는 일]

## Instructions
[Claude가 따를 단계별 가이드]

## Additional Resources
- For details, see [reference.md](reference.md)

## Examples
[입력/출력 예시]
```

---

## Sources

- [Extend Claude with skills](https://code.claude.com/docs/en/skills) - 메인 공식 문서
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) - 플랫폼 문서
- [Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - 작성 가이드
- [Subagents](https://code.claude.com/docs/en/sub-agents) - 서브에이전트 연동
- [github.com/anthropics/skills](https://github.com/anthropics/skills) - 공식 스킬 저장소

---

## Update History

- **2026-02-22**: 공식 문서 전면 재정리 (source of truth 목적)
  - String substitutions 섹션 신규
  - Dynamic context injection (`!`command``) 신규
  - 3단계 로딩 메커니즘 정식화
  - Context budget (2% 규칙) 신규
  - Description best practice 상세화 (3인칭, 1024자)
  - argument-hint 필드 추가
  - Extended thinking (ultrathink) 추가
  - Skill permission control 문법 추가
  - Practical template 추가
  - @file 참조, !command, Plugin/MCP namespace 항목 추가 (slash-commands에서 이관)
- **2026-01-16**: v2.1.x 기능 반영 (context: fork, hooks, progressive disclosure)
- **2025-10-22**: 초기 작성
