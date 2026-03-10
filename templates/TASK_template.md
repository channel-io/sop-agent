```mermaid
flowchart TD
    START([시작]) --> A{분기 조건}
    A -->|조건 A| B[[API 이름\n반환 필드 확인]]:::apiClass
    A -->|조건 B| C[처리 단계]
    B --> D{결과 분기}
    D -->|성공| E([완료])
    D -->|실패/조건| F([상담사 연결])
    C --> E

    classDef successClass fill:#d4edda,stroke:#28a745,stroke-width:2px
    classDef warningClass fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    classDef dangerClass  fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    classDef infoClass    fill:#d1ecf1,stroke:#17a2b8,stroke-width:2px
    classDef processClass fill:#e7f3ff,stroke:#0056b3,stroke-width:2px
    classDef apiClass     fill:#fff0c0,stroke:#e6a817,stroke-width:2px,stroke-dasharray:5 5
```

---

**태스크 {영문자} — {이름}**

| 항목 | 내용 |
|------|------|
| 커버 범위 | {처리하는 상담 유형 설명} |
| 진단 순서 | {분기 조건 순서} |
| API 호출 | `{API 이름}` — {호출 조건} / 없음 |
| ALF 종결 | {자동 완결 케이스 목록} |
| 상담사 연결 | {연결 필요 조건} |
| 상담사 전달 정보 | {전달 정보 목록} |
