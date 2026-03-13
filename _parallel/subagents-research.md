# Sub-agents 공식 문서 변경사항 리서치 결과

기존 가이드 마지막 업데이트: 2026-01-16
리서치 수행일: 2026-02-22

---

## 요약 (3줄 이내)

- 2026년 1월 이후 추가된 핵심 신규 YAML 필드: `memory`, `background`, `isolation`, `mcpServers`, `maxTurns` (5개)
- 신규 기능 3종: isolation worktree 격리 실행, persistent memory, Task(agent_type) 스폰 제한
- 신규 훅 이벤트 4종 추가: `TeammateIdle`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`

---

## 상세 내용

### 1. 신규 YAML 프론트매터 필드

기존 가이드에서 다루지 않은 필드들:

#### `memory` 필드 (v2.1.33에서 추가)
에이전트가 세션 간 지속되는 메모리 디렉토리를 가짐. 지식 축적, 코드베이스 패턴, 디버깅 인사이트 저장.

```yaml
---
name: code-reviewer
description: Reviews code across projects
memory: user
---
```

스코프 옵션:
| 스코프 | 저장 위치 | 용도 |
|--------|-----------|------|
| `user` | `~/.claude/agent-memory/<name>/` | 모든 프로젝트에서 공유 (권장 기본값) |
| `project` | `.claude/agent-memory/<name>/` | 프로젝트 전용, 버전관리 가능 |
| `local` | `.claude/agent-memory-local/<name>/` | 프로젝트 전용, 버전관리 제외 |

메모리 활성화 시 자동 동작:
- 에이전트 시스템 프롬프트에 메모리 읽기/쓰기 지침 포함
- `MEMORY.md` 파일의 첫 200줄을 컨텍스트에 자동 주입
- Read, Write, Edit 툴이 자동으로 활성화됨

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

#### `background` 필드 (v2.1.49에서 추가)
에이전트를 항상 백그라운드 태스크로 실행하도록 선언.

```yaml
---
name: file-monitor
description: Monitors file changes
background: true
---
```

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

#### `isolation` 필드 (v2.1.49~2.1.50에서 추가)
에이전트를 임시 git worktree에서 실행. 변경사항 없으면 worktree 자동 정리.

```yaml
---
name: safe-experimenter
description: Experiments with code in isolation
isolation: worktree
---
```

현재 지원값: `worktree` (유일)

- 출처: https://code.claude.com/docs/en/sub-agents, releasebot.io
- 신뢰도: 1.0 (공식 문서)

#### `mcpServers` 필드
에이전트에서 사용 가능한 MCP 서버 지정. 이미 설정된 서버 이름 참조 또는 인라인 정의 가능.

```yaml
---
name: data-agent
description: Queries databases via MCP
mcpServers:
  - "slack"
  - postgres:
      type: stdio
      command: "mcp-server-postgres"
---
```

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

#### `maxTurns` 필드
에이전트가 멈추기 전 최대 에이전틱 턴 수 제한.

```yaml
---
name: bounded-agent
description: Performs bounded analysis
maxTurns: 10
---
```

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 2. Task(agent_type) 스폰 제한 문법 (v2.1.33)

`claude --agent`로 메인 스레드로 실행될 때 어떤 서브에이전트를 스폰할 수 있는지 제한.

```yaml
---
name: coordinator
description: Coordinates specialized agents
tools: Task(worker, researcher), Read, Bash
---
```

- `Task(worker, researcher)`: worker, researcher만 스폰 허용 (화이트리스트)
- `Task`: 제한 없이 모든 에이전트 스폰 허용
- `tools`에서 `Task` 생략: 어떤 에이전트도 스폰 불가

주의: 이 제한은 `claude --agent`로 실행될 때만 적용. 서브에이전트는 원래 다른 에이전트를 스폰 못하므로 서브에이전트 정의에서는 효과 없음.

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 3. 신규 훅 이벤트

#### `SubagentStart` / `SubagentStop` (기존 `Stop`과 다른 메인 세션 레벨 훅)
settings.json에서 서브에이전트 생명주기에 반응하는 훅. 에이전트 이름으로 매처 사용 가능.

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [{ "type": "command", "command": "./scripts/setup-db.sh" }]
      }
    ]
  }
}
```

#### `Stop` 훅의 자동 변환
프론트매터에서 정의된 `Stop` 훅은 런타임에 자동으로 `SubagentStop` 이벤트로 변환됨.

#### `Stop` / `SubagentStop` 훅에 `last_assistant_message` 추가 (v2.1.47)
훅 입력에 에이전트의 최종 응답 텍스트 포함. 트랜스크립트 파일 파싱 없이 접근 가능.

#### `TeammateIdle` / `TaskCompleted` 훅 이벤트 (v2.1.33)
Agent Teams 기능용 훅 이벤트. 멀티 에이전트 워크플로우에서 사용.
- `TeammateIdle`: 팀메이트가 유휴 상태가 될 때. exit code 2로 작업 계속 강제 가능.
- `TaskCompleted`: 태스크 완료 처리 시. exit code 2로 완료 차단 및 피드백 전송 가능.

#### `WorktreeCreate` / `WorktreeRemove` 훅 이벤트 (v2.1.50)
`isolation: worktree` 사용 시 worktree 생성/삭제에 반응. 커스텀 VCS 설정 및 정리 가능.

#### `ConfigChange` 훅 이벤트 (v2.1.49)
설정 파일 변경 시 발동. 보안 감사 및 선택적 설정 변경 차단용.

- 출처: https://code.claude.com/docs/en/sub-agents, github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- 신뢰도: 1.0 (공식 문서 + 공식 체인지로그)

---

### 4. CLI 변경사항

#### `claude agents` 명령어 (v2.1.50)
인터랙티브 세션 없이 설정된 에이전트 목록 출력. 소스별 그룹화, 오버라이드 표시.

```bash
claude agents
```

기존 `/agents` 슬래시 명령어와 다름. 커맨드라인에서 직접 사용.

#### `--worktree` (`-w`) 플래그 (v2.1.49)
격리된 git worktree에서 Claude 시작.

```bash
claude --worktree
claude -w
```

#### `--disallowedTools`로 내장 에이전트 비활성화
`Task(subagent-name)` 형식으로 특정 에이전트 비활성화.

```bash
claude --disallowedTools "Task(Explore)"
```

또는 settings.json에서:
```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(my-custom-agent)"]
  }
}
```

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 5. 에이전트 색상 설정

`/agents` 인터랙티브 인터페이스에서 에이전트에 배경 색상 지정 가능. UI에서 어떤 에이전트가 실행 중인지 식별하는 데 사용.

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 6. `--agents` JSON 플래그의 전체 필드 명세 명확화

기존 가이드에서는 일부 필드만 언급. 공식 문서에서 JSON 플래그가 지원하는 전체 필드:
`description`, `prompt`, `tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `memory`

JSON 플래그에서는 마크다운 본문 대신 `prompt` 키 사용.

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 7. 트랜스크립트 저장 경로 및 자동 정리

서브에이전트 트랜스크립트는 메인 대화와 독립적으로 저장:
- 저장 위치: `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`
- 자동 정리: `cleanupPeriodDays` 설정 기준 (기본값: 30일)
- 메인 대화 컴팩션 시에도 서브에이전트 트랜스크립트는 영향 없음

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 8. 컴팩션 로그 형식

서브에이전트 트랜스크립트 내 컴팩션 이벤트 로그:

```json
{
  "type": "system",
  "subtype": "compact_boundary",
  "compactMetadata": {
    "trigger": "auto",
    "preTokens": 167189
  }
}
```

`preTokens`: 컴팩션 전 사용된 토큰 수.

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 9. 백그라운드 에이전트 동작 변경 (v2.1.47)

- ESC 키로 메인 스레드 취소 시 백그라운드 에이전트는 계속 실행됨 (이전과 다른 동작)
- Ctrl+F로 백그라운드 에이전트 종료 (두 번 눌러 확인)
- 백그라운드 에이전트에서 MCP 툴 사용 불가 (기존에도 있었으나 명시적으로 문서화)

- 출처: releasebot.io, github changelog
- 신뢰도: 0.9 (공식 체인지로그 기반 요약)

---

### 10. 빌트인 에이전트 추가

기존 가이드의 빌트인: Explore, Plan, General-purpose, Bash
추가된 빌트인:

| 에이전트 | 모델 | 사용 시점 |
|----------|------|-----------|
| statusline-setup | Sonnet | `/statusline` 실행 시 |
| Claude Code Guide | Haiku | Claude Code 기능 관련 질문 시 |

- 출처: https://code.claude.com/docs/en/sub-agents
- 신뢰도: 1.0 (공식 문서)

---

### 11. Agent Teams (신규 기능, 실험적)

서브에이전트와 별개의 새로운 멀티 에이전트 기능. 서브에이전트 문서에서 구분됨.

- 활성화: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 환경 변수
- 특징: 팀메이트 간 직접 메시지, 공유 태스크 리스트, 독립 컨텍스트 창
- 서브에이전트와의 차이: 팀메이트끼리 직접 통신 가능 (서브에이전트는 메인 에이전트에만 보고)

서브에이전트 가이드 업데이트 시 Agent Teams는 별도 문서 참조로 안내하는 것이 적절.

- 출처: https://code.claude.com/docs/en/agent-teams
- 신뢰도: 1.0 (공식 문서)

---

## 소스 평가표

| # | 소스 | 유형 | 신뢰도 | 최신성 | 관련성 |
|---|------|------|--------|--------|--------|
| 1 | https://code.claude.com/docs/en/sub-agents | 공식 문서 | 1.0 | 최신 (2026-02) | 1.0 |
| 2 | https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md | 공식 체인지로그 | 1.0 | 최신 (v2.1.50) | 0.95 |
| 3 | https://releasebot.io/updates/anthropic/claude-code | 릴리즈 추적 | 0.8 | 최신 (2026-02) | 0.9 |
| 4 | https://code.claude.com/docs/en/agent-teams | 공식 문서 | 1.0 | 최신 | 0.7 |
| 5 | https://www.gradually.ai/en/changelogs/claude-code/ | 체인지로그 요약 | 0.7 | 최신 | 0.85 |

---

## 한계 및 추가 조사 필요 사항

- `isolation` 필드의 정확한 버전 도입 시점이 v2.1.49와 v2.1.50 사이에 걸쳐 있어 명확하지 않음
- `mcpServers` 필드가 기존 가이드에 없었는지, 아니면 문서화가 새로 된 것인지 불명확
- `TeammateIdle`/`TaskCompleted` 훅은 Agent Teams 기능에 속하므로, 서브에이전트 가이드 범위인지 판단 필요
- `skills` 프론트매터의 "전체 콘텐츠 주입" 동작이 기존 가이드에서 충분히 설명되었는지 불명확

---

## 메인 세션 전달 사항

- 통합 시 참고할 포인트: 신규 YAML 필드 5개(memory, background, isolation, mcpServers, maxTurns)가 핵심 추가 내용. 기존 가이드의 YAML 필드 테이블 업데이트 필요.
- 다른 작업과의 연결점: Agent Teams는 서브에이전트와 다른 별도 기능이므로 가이드에서 구분 안내 추가 권장
- 미결정 사항: isolation 필드 버전 도입 시점 확인 필요. skills 필드 설명의 "전체 콘텐츠 주입" 동작이 기존 가이드에서 명확히 설명되었는지 확인 필요.
- 가장 중요한 신규 기능 우선순위: (1) isolation: worktree, (2) memory 필드, (3) Task(agent_type) 스폰 제한, (4) last_assistant_message 훅 필드
