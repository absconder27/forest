---
description: 일간 매출 보고서 생성 및 내 메일로 발송
allowed-tools: Read, Write, Edit, Bash
---

일간 매출 보고서를 생성하고 내 메일(forest@grandeclipfnb.com)로 발송합니다.
규림님이 메일에서 그래프 삽입/수정 후 경영진에게 직접 전달합니다.

**인자**: $ARGUMENTS (선택)
- 비어있으면: 어제 날짜 기준
- 날짜 (예: 2026-03-15): 해당 날짜 기준

**수행할 작업:**

1. 스크립트 실행:
   ```
   ./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/gws/daily_sales_report.py --date {날짜} --send-email
   ```
   - 인자가 비어있으면 `--date` 생략 (어제 자동)
   - `--send-email`은 항상 포함 (본인 메일로 발송)

2. 결과 표시:
   - 생성된 리포트 텍스트 표시
   - 발송 완료 메시지 표시
   - "(그래프)" 표시된 곳에 스크린샷을 넣으라고 안내
