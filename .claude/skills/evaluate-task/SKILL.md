---
name: evaluate-task
description: Task JSON 품질 평가. 검증 및 품질 점수를 제공합니다.
---

# Task JSON 품질 평가

## 작업 순서

### 1. 입력 확인
- 입력 요청: "📋 평가할 Task JSON 파일을 공유해주세요."

### 2. 검증 기준 파일 Read

Read 툴로 아래 파일들을 읽는다:
- ax-resources/prompts/task/04_evaluation/methodology.md
- ax-resources/specs/task/policies/task-policy.md
- ax-resources/specs/task/definitions/spec-prod.md

### 3. 검증 수행

methodology.md의 "1.2 검증 수행 방법"을 따른다.

검증 원칙:
- 첫 번째 판정을 최종 결과로 사용한다
- 검증 통과 시: "검증 통과" 한 줄 출력 후 품질 평가 진행
- 검증 실패 시: 위반 항목만 출력하고 종료

### 4. 품질 평가 기준 파일 Read

검증 통과 시에만 실행한다.

Read 툴로 아래 파일들을 읽는다:
- ax-resources/prompts/task/03_execution/knowledge/*.md

### 5. 품질 평가 수행

- 각 노드를 실제로 분석하여 영역별 10점 만점 채점
- knowledge 파일에 명시된 규칙만 감점 기준으로 사용

### 6. 결과 출력

- 최종 결과만 출력한다
- 출력 형식: ax-resources/prompts/task/04_evaluation/examples/output-sample.txt
