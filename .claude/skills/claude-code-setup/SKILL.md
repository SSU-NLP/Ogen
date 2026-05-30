---
name: claude-code-setup
description: "Claude Code 프로젝트 초기 설정과 작업 환경 구축을 도와주는 스킬. CLAUDE.md 작성, .claude/ 폴더 구조 생성, settings.json 권한 설정, hooks 구성, skills/plugins 기본 구조 잡기, Cowork 폴더 설계를 포함한다. 사용자가 'Claude Code 세팅', 'CLAUDE.md 만들어줘', '.claude 폴더 구조', 'Claude Code 초기 설정', 'Cowork 폴더 구조', '프로젝트 규칙 파일', 'hooks 설정', 'settings.json', 'Claude Code 온보딩', '작업 환경 세팅', 'plan.md 만들기', 'handoff.md', 'context engineering 설정' 등을 요청할 때 반드시 이 스킬을 사용하세요. Claude Code나 Cowork를 처음 시작하는 사람, 팀 표준 환경을 만들려는 리드, 기존 프로젝트에 Claude Code를 붙이려는 개발자 모두에게 적용된다."
---

# Claude Code 프로젝트 설정 스킬

이 스킬은 Claude Code와 Cowork의 작업 환경을 체계적으로 구축한다. 핵심 원칙: **프롬프트를 잘 쓰는 것보다, 문맥·도구·권한·검증 루프를 잘 설계하는 것이 Claude 활용의 승패를 가른다.**

## 작업 흐름

### 1단계: 사용자 상황 파악

먼저 아래를 확인한다:
- **대상 제품**: Claude Code (개발자) vs Cowork (비개발자) vs 둘 다
- **프로젝트 유형**: 새 프로젝트 vs 기존 저장소에 붙이기
- **팀 규모**: 개인 vs 팀 (팀이면 managed settings 고려)
- **주요 언어/스택**: 빌드·테스트·린트 명령이 달라짐

### 2단계: Claude Code 설정 (개발자용)

#### CLAUDE.md 작성

CLAUDE.md는 **운영 계약서**다. 위키가 아니다. 항상 읽히는 문서이므로 핵심만 남긴다.

필수 섹션:
```markdown
# Project Contract

## What This Repo Is
- 한 줄 설명

## Commands
- install: `pnpm install`
- dev: `pnpm dev`
- test: `pnpm test`
- lint: `pnpm lint`

## Boundaries
- 주요 디렉터리 역할 설명 (src/api/, src/domain/ 등)

## Safety
- never edit `.env*`
- never push without tests
- always show diff before commit
- do not claim done unless tests pass
```

**넣지 말 것**: 전체 API 문서, 긴 배경 설명, 드물게 쓰는 절차. 이런 건 rules나 skills로 뺀다.

#### .claude/ 폴더 구조

```
.claude/
├── settings.json          # 권한 경계
├── settings.local.json    # 개인 설정 (gitignore 대상)
├── rules/                 # path-specific 규칙
│   ├── api.md
│   ├── frontend.md
│   └── tests.md
├── skills/                # 반복 작업 절차
│   └── code-review/
│       └── SKILL.md
└── hooks.json             # 자동 개입 규칙
```

#### settings.json 권한 설정

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "Bash(pnpm test:*)",
      "Bash(pnpm lint)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Bash(rm -rf *)"
    ]
  }
}
```

설정 우선순위: **Managed > Command line > Local > Project > User**. 조직이 위에서 잠근 규칙은 개인 설정으로 덮어쓸 수 없다.

#### Path-specific Rules 예시

`.claude/rules/api.md`:
```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/handlers/**/*.ts"
---
# API Rules
- validate all request bodies with zod
- return `{ data, error }` format
- never expose internal stack traces
```

이렇게 하면 API 파일을 건드릴 때만 이 규칙이 활성화된다.

#### Hooks 설정

`.claude/hooks.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-dangerous.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "pnpm lint --quiet"
          }
        ]
      }
    ]
  }
}
```

Hook 유형: command hook, prompt-based hook, agent-based hook, HTTP hook. 가장 쉬운 것부터 시작한다.

#### plan.md와 handoff.md

큰 작업을 시작할 때 `plan.md`를 먼저 만든다:
```markdown
# Plan: [작업명]
## Goal
## Inputs
## Done When
- [ ] 기준 1
- [ ] 기준 2
## Steps
- [ ] step 1
- [ ] step 2
```

세션이 끝날 때 `handoff.md`를 남긴다:
```markdown
# Handoff
## What changed
## What passed
## What failed / blocked
## Next step
```

### 3단계: Cowork 설정 (비개발자용)

#### 폴더 구조

```
CLAUDE-COWORK/
├── ABOUT-ME/
│   ├── about-me.md          # 역할, 상황, 배경
│   ├── working-rules.md     # 작업 태도 규칙
│   └── brand-voice.md       # 말투, 톤앤매너
├── PROJECTS/
│   ├── project-a/
│   │   ├── brief.md
│   │   └── sources/
│   └── project-b/
├── TEMPLATES/
│   └── weekly-brief-template.md
├── CLAUDE-OUTPUTS/
└── HANDOFF/
```

각 폴더 역할:
- **ABOUT-ME/**: 신입에게 건네는 팀 소개 문서. Claude가 나를 대신할 때의 기준.
- **PROJECTS/**: 프로젝트별 서류함. 고객·주제별로 분리.
- **TEMPLATES/**: 쿠키 틀. 내용은 매번 달라도 구조는 유지.
- **CLAUDE-OUTPUTS/**: 결재 대기함. 검토할 결과만 모임.
- **HANDOFF/**: 인수인계 노트. 다음 세션이 이어받을 단서.

#### Global Instructions

Cowork에 아래를 설정한다:
```
Before every task:
- read ABOUT-ME/ first
- if a matching project exists, read it before execution
- save outputs only in CLAUDE-OUTPUTS/
- ask short clarifying questions if the brief is incomplete
- use templates from TEMPLATES/ when a matching one exists
```

#### about-me.md 예시

```markdown
# About Me
- 현재 역할과 책임
- 주로 다루는 업무 (보고서, 리서치, 고객 커뮤니케이션 등)
- 선호하는 문체 (간결, 구조적, 데이터 기반 등)
- 싫어하는 표현 (AI스러운 문구, 과장, 빈 수사)
```

#### working-rules.md 예시

```markdown
# Working Rules
- 불완전한 브리프면 AskUserQuestion으로 먼저 질문
- 파일 삭제는 승인 없이 금지
- 모든 산출물은 CLAUDE-OUTPUTS/에 저장
- 불확실한 정보는 명시적으로 표시
- 외부 발송 콘텐츠는 초안까지만 생성
```

### 4단계: Skills 만들기

반복되는 작업이 보이면 스킬로 올린다. Agent Skills 오픈 표준을 따른다.

스킬 폴더 구조:
```
my-skill/
├── SKILL.md              # 필수: YAML frontmatter + 지침
├── scripts/              # 선택: 실행 코드
├── references/           # 선택: 참고 문서
├── assets/               # 선택: 템플릿, 리소스
└── examples/             # 선택: 잘된 결과 예시
```

SKILL.md frontmatter 필수 필드:
- `name`: 소문자, 하이픈만, 64자 이내, 폴더명과 일치
- `description`: 1024자 이내. **무엇을 하는지 + 언제 쓰는지** 둘 다 포함

Progressive disclosure 원칙:
1. **Metadata** (~100 토큰): name + description → 항상 로드
2. **Instructions** (<5000 토큰 권장): SKILL.md 본문 → 스킬 활성화 시 로드
3. **Resources** (필요시): scripts/, references/, assets/ → 필요할 때만 로드

스킬을 만들 타이밍:
- 같은 설명을 3번 이상 반복하고 있을 때
- 결과 형식이 반복될 때 (회의록, 브리프, PRD, 코드 리뷰)
- 사람마다 편차를 줄여야 할 때

### 5단계: 도입 우선순위

**개인 개발자**: CLAUDE.md + rules → hooks + lint → handoff/plan → skills → MCP

**비개발 실무자**: 폴더 구조 + context files → 템플릿 → plugins 1~2개 → scheduled tasks

**팀 리드**: 팀 공용 CLAUDE.md + rules → skill/plugin 기준 → org permissions → remote control + channels

순서를 지키는 이유: 문맥과 규칙이 먼저 고정되어야 skill과 plugin이 일관되게 동작한다. 외부 연결과 자동화는 맨 마지막에 붙여야 사고 반경을 관리하기 쉽다.

## Gotchas

- CLAUDE.md를 백과사전처럼 길게 쓰지 마라. 항상 읽히는 문서에 잡음이 많으면 핵심 규칙이 묻힌다.
- MCP를 많이 붙인다고 좋아지지 않는다. 자주 쓰는 경로만 열어라.
- 세션 하나에 모든 일을 몰아넣지 마라. 역할이 다르면 세션을 나눠라.
- tool output이 context를 가장 빨리 죽인다. 긴 로그는 요약하거나 tail로 잘라라.
- "완료"를 말로 두지 말고 verification plan이나 hook으로 고정하라.
- Cowork scheduled task는 데스크톱 앱이 열려 있어야 돌아간다.
- 처음부터 모든 기능을 켜지 마라. 작은 성공을 먼저 만들어라.

## 참고

더 자세한 내용은 `references/` 폴더를 참조:
- `references/context-engineering.md`: 문맥 설계 심화
- `references/four-layers.md`: 지식·도구·패키지·통제 4계층 모델
