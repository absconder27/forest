# Claude Code Slash Commands 문서 현황 리서치 결과

> 리서치 일시: 2026-02-22
> 대상 문서: `/Users/rhim/Projects/pkm/30-knowledge/37-claude-code/37.00-official-docs/slash-commands-guide.md`
> 기존 문서 최종 업데이트: 2026-01-16

---

## 요약 (3줄 이내)

- `https://code.claude.com/docs/en/slash-commands` URL은 `/skills` 페이지로 리다이렉트되며, 공식 문서에 별도 slash commands 페이지는 더 이상 존재하지 않는다.
- 공식 문서가 "Custom slash commands have been merged into skills"를 명시적으로 선언했으며, `.claude/commands/`는 하위 호환성 유지만 보장한다.
- `slash-commands-guide.md`의 핵심 내용(arguments, !command, @file, Skill tool 호출 등) 중 대부분이 `skills-guide.md`에 이미 통합되어 있어, 별도 유지 가치가 줄었다.

---

## 상세 내용

### 1. URL 리다이렉트 확인

- `https://code.claude.com/docs/en/slash-commands` 요청 시 반환 페이지 타이틀: **"Extend Claude with skills"**
- 페이지 서브타이틀: "Create, manage, and share skills to extend Claude's capabilities in Claude Code. **Includes custom slash commands.**"
- 결론: slash-commands URL은 skills 페이지로 완전히 통합됨. 별도 slash commands 문서 페이지 없음.
- 출처: https://code.claude.com/docs/en/slash-commands (리다이렉트 확인)
- 신뢰도: 1.0 (공식 문서)

### 2. 공식 문서의 통합 선언

skills 페이지 상단 Note에서 명시:

> **Custom slash commands have been merged into skills.** A file at `.claude/commands/review.md` and a skill at `.claude/skills/review/SKILL.md` both create `/review` and work the same way. Your existing `.claude/commands/` files keep working. Skills add optional features: a directory for supporting files, frontmatter to [control whether you or Claude invokes them], and the ability for Claude to load them automatically when relevant.

또한:

> Files in `.claude/commands/` still work and support the same frontmatter. **Skills are recommended** since they support additional features like supporting files.

- 출처: https://code.claude.com/docs/en/skills
- 신뢰도: 1.0 (공식 문서)

### 3. Built-in Commands 위치 이동

공식 문서에서 built-in commands의 위치:

> For built-in commands like `/help` and `/compact`, see [interactive mode](/en/interactive-mode#built-in-commands).

- 내장 커맨드(`/clear`, `/compact`, `/context`, `/help` 등)는 이제 **interactive-mode 페이지**에서 관리됨
- `https://code.claude.com/docs/en/interactive-mode#built-in-commands`
- 출처: https://code.claude.com/docs/en/interactive-mode
- 신뢰도: 1.0 (공식 문서)

### 4. 기존 slash-commands-guide.md vs skills-guide.md 커버리지 비교

| 기존 slash-commands-guide.md 섹션 | skills-guide.md 커버 여부 |
|----------------------------------|--------------------------|
| Built-in Commands 목록 | 미포함 (interactive-mode로 이동) |
| Custom Commands 파일 구조 | 포함 (§2 파일 구조) |
| YAML Frontmatter 전체 필드 | 포함 (§3 Frontmatter) |
| `$ARGUMENTS`, `$1`, `$2` 변수 | 포함 (§6 String Substitutions) |
| `!command` bash 실행 | 포함 (§7 Dynamic Context Injection) |
| `@file` 참조 | 미포함 (skills-guide에 없음) |
| Skill Tool 프로그래매틱 호출 | 포함 (§12 Permission Control 내) |
| context: fork | 포함 (§8) |
| hooks | 포함 (§10) |
| Plugin Commands | 미포함 |
| MCP Slash Commands | 미포함 |
| Commands vs Skills 비교표 | 포함 (§18) |
| Namespace commands (subdirectory) | 미포함 |

**skills-guide.md에 없고 slash-commands-guide.md에만 있는 내용:**
- `@file` 참조 문법
- Plugin Commands (`/plugin-name:command-name`)
- MCP Slash Commands (`/mcp__server__prompt` 형식)
- `.claude/commands/` 서브디렉토리 네임스페이스
- Built-in Commands 상세 목록 (이제 interactive-mode로)

### 5. 2026년 1월 이후 changelog 변경사항

공식 GitHub CHANGELOG.md 및 code.claude.com/docs/en/changelog 검토 결과:

- v2.1.41 ~ v2.1.50 (2025년 12월 ~ 2026년 현재): slash commands 또는 skills 시스템의 구조적 변경 없음
- 새 기능: `claude agents` CLI 커맨드, worktree isolation, Ctrl+F 단축키, 플러그인 즉시 사용 가능
- `/slash-commands` URL 리다이렉트 시점은 2026-01-16 이전에 이미 발생한 것으로 추정 (skills 페이지가 이미 통합 내용 포함)
- 출처: https://code.claude.com/docs/en/changelog, https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- 신뢰도: 0.9 (공식 changelog이나 정확한 날짜 특정 불가)

### 6. skills-guide.md 현재 상태

`/Users/rhim/Projects/pkm/30-knowledge/37-claude-code/37.00-official-docs/skills-guide.md`:
- 최종 업데이트: **2026-02-22** (오늘)
- 이미 source of truth로 선언됨
- 20개 섹션으로 구성, 공식 문서 전체 내용 커버
- String substitutions, Dynamic context injection, 3단계 로딩 메커니즘 등 신규 내용 포함

---

## 소스 평가표

| # | 소스 | 유형 | 신뢰도 | 최신성 | 관련성 |
|---|------|------|--------|--------|--------|
| 1 | https://code.claude.com/docs/en/slash-commands | 공식 문서 | 1.0 | 2026-02 | 1.0 |
| 2 | https://code.claude.com/docs/en/skills | 공식 문서 | 1.0 | 2026-02 | 1.0 |
| 3 | https://code.claude.com/docs/en/interactive-mode | 공식 문서 | 1.0 | 2026-02 | 0.9 |
| 4 | https://code.claude.com/docs/en/changelog | 공식 changelog | 0.9 | 2026-02 | 0.8 |
| 5 | https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md | 공식 레포 | 0.9 | 2025-12 | 0.7 |
| 6 | 기존 slash-commands-guide.md (PKM) | 내부 문서 | 0.8 | 2026-01-16 | 1.0 |
| 7 | 기존 skills-guide.md (PKM) | 내부 문서 | 0.9 | 2026-02-22 | 1.0 |

---

## 한계 및 추가 조사 필요 사항

- **정확한 리다이렉트 시점 불명확**: `/slash-commands` URL이 언제부터 `/skills`로 리다이렉트되었는지 changelog에서 명시적 언급 없음. 2026-01-16 이전부터였을 가능성 있음.
- **`@file` 참조 문법 위치**: 현재 skills-guide.md에 `@file` 문법이 없음. interactive-mode 또는 별도 위치에 있을 수 있음 - 추가 확인 필요.
- **Plugin Commands 문서화 현황**: `skills-guide.md`에 plugin commands 관련 내용이 빠져 있음. 플러그인 페이지에서 다루는지 확인 필요.

---

## 메인 세션 전달 사항

### 핵심 판단

**slash-commands-guide.md를 별도 유지하는 것은 비권장**. 이유:

1. 공식 URL 리다이렉트 자체가 통합을 선언함
2. 공식 문서가 명시적으로 "merged into skills"라고 선언
3. skills-guide.md가 이미 2026-02-22에 source of truth로 재정비됨
4. 핵심 기능(frontmatter, arguments, !command, context:fork, hooks)은 모두 skills-guide.md에 있음

### 권장 처리 방안 (3가지 옵션)

**Option A - 통합 (권장)**: slash-commands-guide.md를 deprecated 처리 후, 누락된 내용만 skills-guide.md에 추가
- 추가할 내용: `@file` 참조 문법, MCP Slash Commands 패턴, Plugin Commands 네임스페이스
- slash-commands-guide.md에 deprecation notice 추가 후 90-archive로 이동

**Option B - 부분 유지**: slash-commands-guide.md를 "Built-in Commands 참조" 용도로만 축소 유지
- Built-in commands 목록이 interactive-mode에 있어서 필요성이 낮음
- 비권장

**Option C - 완전 삭제**: slash-commands-guide.md를 즉시 archive 이동
- 가장 단순하지만 `@file`, MCP commands, Plugin commands 정보 손실 위험

### 다른 작업과의 연결점

- skills-guide.md 업데이트 작업과 직접 연결
- `@file` 문법 확인을 위해 interactive-mode 페이지 재검토 필요

### 미결정 사항

- `@file` 참조 문법을 skills-guide.md에 추가할지, 별도 "interactive features" 섹션으로 다룰지
- MCP slash commands(`/mcp__server__prompt`) 패턴을 skills-guide.md에 넣을지 mcp-guide.md에 넣을지
- 통합 후 내부 다른 문서들의 `[[slash-commands-guide]]` 링크 처리
