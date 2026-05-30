# 지식·도구·패키지·통제 4계층 모델

Claude 생태계는 네 축으로 나누면 선명해진다.

## 1. 지식 레이어

Claude가 무엇을 알고 어떤 규칙으로 움직여야 하는지.

- CLAUDE.md, rules, memory, project context
- examples, skill instructions
- 비유: 팀 운영 매뉴얼, 업무 인수인계 문서

## 2. 도구 레이어

Claude가 실제로 무엇을 할 수 있는지.

- Bash, Read/Edit/Write, MCP tool, connector
- Browser/computer use, scheduled tasks
- 비유: 프린터, 메신저, 드라이브, 출입카드

## 3. 패키지 레이어

지식과 도구를 묶어서 재사용 가능한 형태로 배포.

- Skill: 반복 작업 절차 ("하는 법")
- Plugin: Skill + commands + agents + hooks + MCP를 함께 배포 ("역할 설치 패키지")
- 비유: 새 팀원 온보딩 박스

## 4. 통제 레이어

Claude가 잘못된 방향으로 새지 않게 막고 검증.

- permissions, hooks, approvals, plan mode
- worktree, tests, review agent
- 비유: 결재선, 잠금장치, 자동 검사

## 실무 예시

**요청: "매주 경쟁사 브리프를 자동으로 만들어 달라"**

| 레이어 | 역할 |
|--------|------|
| 지식 | 브리프 구조 템플릿, 경쟁사 목록, "지난 7일만" 규칙 |
| 도구 | 웹 검색, Drive/Notion connector, 저장 경로 |
| 패키지 | weekly-brief skill 또는 plugin |
| 통제 | 행동 제안 3개 이하, 출처·날짜 필수, 외부 발송 전 사람 검토 |

## 한 레이어 문제를 다른 레이어에서 풀면 안 된다

- 권한 문제를 프롬프트로 해결하려 하면 빈틈이 생긴다
- 절차 문제를 connector 설치만으로 해결하려 하면 한계가 온다
- 반복 작업 문제를 매번 긴 프롬프트로 해결하면 불안정하다

## Skill vs MCP vs Plugin 한 줄 판단법

- "매번 같은 형식으로 하게 만들고 싶다" → Skill
- "Slack, Drive, GitHub 같은 바깥 도구에 닿아야 한다" → MCP/Connector
- "팀 전체가 같은 구성으로 바로 쓰게 하고 싶다" → Plugin
- "실수하면 안 되고 승인이나 자동 검사가 필요하다" → Hooks/permissions (통제 레이어)
