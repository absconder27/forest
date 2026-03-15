# .claude/rules/ - Source of Truth

> **Source**: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)
> **Updated**: 2026-02-22
> **Purpose**: .claude/rules/ 시스템 유일한 참조 문서

---

## 1. 개요

`.claude/rules/` 디렉토리는 CLAUDE.md를 여러 파일로 모듈화하여 관리. 모든 `.md` 파일이 자동 로드됨. 서브디렉토리도 재귀 탐색.

---

## 2. 기본 구조

```
your-project/
├── .claude/
│   ├── CLAUDE.md
│   └── rules/
│       ├── code-style.md
│       ├── testing.md
│       ├── security.md
│       ├── frontend/
│       │   └── react.md
│       └── backend/
│           └── api.md
```

---

## 3. 저장 위치 및 우선순위

| 위치 | 경로 | 적용 범위 |
|------|------|----------|
| 프로젝트 | `./.claude/rules/*.md` | 해당 프로젝트 |
| 사용자 | `~/.claude/rules/*.md` | 모든 프로젝트 |

**우선순위** (높음 -> 낮음):
1. Enterprise policy
2. 프로젝트 CLAUDE.md
3. 프로젝트 rules
4. 사용자 CLAUDE.md
5. 사용자 rules
6. CLAUDE.local.md

`paths` 필드가 없는 규칙은 모든 파일에 무조건 적용.

---

## 4. 조건부 규칙 (Path-Specific Rules)

YAML frontmatter로 특정 파일에만 규칙 적용 가능.

### 작동하는 형식

```markdown
---
globs: **/*.ts, src/**/*.tsx
---

# API 개발 규칙
- 모든 API 엔드포인트에 입력 검증 필수
```

### 주의: paths vs globs 필드 버그

공식 문서는 `paths:` 필드를 설명하지만, **실제로는 YAML 배열 형식이 작동하지 않는 버그**가 있음 (Issue #17204).

```yaml
# 미작동 - YAML 배열
paths:
  - "src/**/*.ts"

# 미작동 - 따옴표 있는 단일 값
paths: "**/*.ts"

# 작동 - 따옴표 없는 단일 값 (제한적)
paths: **/*.ts

# 권장 - globs 필드 사용 (CSV 형식)
globs: **/*.ts, src/**/*.tsx
```

**현재 권장**: `globs:` 필드를 CSV 형식으로 사용하는 것이 가장 안정적.

### 알려진 제한사항

1. **user-level paths 미작동**: `~/.claude/rules/`에서 `paths:` / `globs:` 조건부 로딩이 완전히 비작동 (Issue #21858, 미해결)
2. **세션 내 해제 안 됨**: 한 번 로드된 조건부 규칙은 다른 디렉토리로 이동해도 세션 내에서 계속 활성 (Issue #16299, 미해결)
3. **Git worktree 무시**: Worktree 내에서 paths/globs 필터링이 무시됨 (Issue #23569)

### Glob 패턴

| 패턴 | 매칭 대상 |
|------|-----------|
| `**/*.ts` | 모든 디렉토리의 TypeScript 파일 |
| `src/**/*` | src/ 하위 모든 파일 |
| `*.md` | 프로젝트 루트의 마크다운 파일 |
| `**/*.{ts,tsx}` | ts와 tsx 파일 모두 |
| `{src,lib}/**/*.ts` | src와 lib 디렉토리 |

---

## 5. --add-dir 디렉토리 rules 로딩 (v2.1.20)

추가 디렉토리의 rules도 로드 가능:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

공유 규칙 저장소를 여러 프로젝트에서 참조할 때 유용.

---

## 6. @import 활용

rules 파일에서 외부 문서 참조 가능:

```markdown
# Subagent 작성 규칙

@/path/to/official-docs/subagents-guide.md

## 추가 규칙
- 프로젝트 특화 규칙...
```

Recursive import 최대 깊이: 5 hops.

---

## 7. Symlink 활용

여러 프로젝트에서 공통 규칙 공유:

```bash
# 공유 rules 디렉토리 심링크
ln -s ~/shared-claude-rules .claude/rules/shared

# 개별 규칙 파일 심링크
ln -s ~/company-standards/security.md .claude/rules/security.md
```

순환 심링크는 자동 감지되어 안전하게 처리.

---

## 8. Best Practice

### DO

- 주제별 분리: 각 파일은 하나의 주제만 (testing.md, api-design.md)
- 명확한 파일명: 파일명만으로 내용 파악 가능
- 조건부 규칙은 `globs:` CSV 형식 사용
- 정기적 검토: 프로젝트 변화에 맞춰 갱신

### DON'T

- 모든 규칙을 조건부로 만들기
- 너무 세분화된 파일 구조
- 중복되는 규칙
- user-level rules에서 조건부 규칙 의존 (현재 미작동)

---

## 9. 일반적인 규칙 구성

| 파일 | 용도 |
|------|------|
| `code-style.md` | 코드 스타일, 포맷팅 |
| `testing.md` | 테스트 작성 컨벤션 |
| `security.md` | 보안 요구사항 |
| `git.md` | Git 워크플로우 |
| `api-design.md` | API 설계 원칙 |

---

## Sources

- [Manage Claude's memory](https://code.claude.com/docs/en/memory)
- [Issue #17204 - globs vs paths](https://github.com/anthropics/claude-code/issues/17204)
- [Issue #16299 - paths scope bug](https://github.com/anthropics/claude-code/issues/16299)
- [Issue #21858 - user-level paths](https://github.com/anthropics/claude-code/issues/21858)

## Related

- [[claude-md-guide]] - CLAUDE.md 가이드
- [[skills-guide]] - Skills 시스템 가이드

---

## Update History

- **2026-02-22**: 전면 갱신 (source of truth 목적)
  - paths vs globs 버그 경고 추가 (Issue #17204)
  - user-level 조건부 규칙 미작동 명시 (Issue #21858)
  - Git worktree 제한사항 추가 (Issue #23569)
  - --add-dir rules 로딩 (v2.1.20)
  - Auto Memory 교차 참조 제거 (claude-md-guide에서 다룸)
- **2026-01-19**: 초기 작성
