---
description: 일간 매출 보고서 생성 및 이메일 발송
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

일간 매출 보고서를 생성하고, 확인 후 이메일로 발송합니다.

**인자**: $ARGUMENTS (선택)
- 비어있으면: 어제 날짜 기준
- 날짜 (예: 2026-03-15): 해당 날짜 기준

**수행할 작업:**

1. **리포트 생성**
   - 스크립트 실행:
     ```
     ./00-system/02-scripts/gws/venv/bin/python3 ./00-system/02-scripts/gws/daily_sales_report.py --date {날짜}
     ```
   - 인자가 비어있으면 `--date` 생략 (어제 자동)
   - 생성된 리포트를 사용자에게 표시

2. **수동 입력 확인**
   리포트에 "(수동 입력)" 표시된 항목이 있으면 사용자에게 물어보기:
   - 날씨 정보 (예: "맑음, 최고 15도 / 최저 5도")
   - 특이사항 (예: "롯데면세점 일매출 3,146불")
   - ROAS (예: "233%")
   - 건단가, 결제건수 (있으면)

   사용자가 "스킵" 또는 "없음"이라고 하면 해당 항목 제거

3. **리포트 수정**
   수동 입력값을 반영하여 리포트 텍스트 최종 확정
   사용자에게 최종본 표시

4. **발송 확인**
   AskUserQuestion으로 확인:
   - "내 메일로 테스트 발송" (forest@grandeclipfnb.com)
   - "경영진에게 발송" (hibong@grandeclip.com, snowspring@grandeclip.com)
   - "발송 안 함"

5. **이메일 발송** (사용자가 선택한 경우)
   - 테스트: `--send-email --to forest@grandeclipfnb.com`
   - 경영진: `--send-email --to "hibong@grandeclip.com,snowspring@grandeclip.com"`

   **주의**: 경영진 발송은 반드시 사용자 확인 후에만 실행

6. **결과 보고**
   - 발송 성공/실패 여부
   - 메일 제목: [뉴믹스][일간]MMDD
