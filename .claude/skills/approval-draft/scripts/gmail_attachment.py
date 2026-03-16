#!/usr/bin/env python3
"""
Gmail 메일 검색 + 첨부파일 다운로드 스크립트

사용법:
    python3 gmail_attachment.py search "키워드" --limit 5
    python3 gmail_attachment.py fetch <message_id> --output /tmp/approval-draft/
"""

import argparse
import base64
import os
import sys
from pathlib import Path

# gws_auth 모듈 임포트
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "00-system" / "02-scripts" / "gws"))
from gws_auth import get_service


def search_mail(query: str, limit: int = 5) -> list[dict]:
    """Gmail에서 메일을 검색하여 목록을 반환합니다."""
    service = get_service("gmail")
    results = service.users().messages().list(
        userId="me", q=query, maxResults=limit
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print("검색 결과가 없습니다.")
        return []

    mail_list = []
    for msg_info in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_info["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        has_attachments = any(
            part.get("filename")
            for part in msg["payload"].get("parts", [])
            if part.get("filename")
        )

        entry = {
            "id": msg_info["id"],
            "subject": headers.get("Subject", "(제목 없음)"),
            "from": headers.get("From", "(발신자 없음)"),
            "date": headers.get("Date", "(날짜 없음)"),
            "has_attachments": has_attachments,
        }
        mail_list.append(entry)

    # 결과 출력
    for i, m in enumerate(mail_list, 1):
        attach_mark = " [첨부]" if m["has_attachments"] else ""
        print(f"{i}. {m['subject']}{attach_mark}")
        print(f"   발신: {m['from']}")
        print(f"   날짜: {m['date']}")
        print(f"   ID: {m['id']}")
        print()

    return mail_list


def fetch_mail(message_id: str, output_dir: str = "/tmp/approval-draft/") -> dict:
    """메일 본문과 첨부파일을 다운로드합니다."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    service = get_service("gmail")
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    subject = headers.get("Subject", "(제목 없음)")
    sender = headers.get("From", "(발신자 없음)")
    date = headers.get("Date", "(날짜 없음)")

    print(f"제목: {subject}")
    print(f"발신: {sender}")
    print(f"날짜: {date}")
    print()

    # 본문 추출
    body_text = _extract_body(msg["payload"])
    body_file = output_path / "body.txt"
    body_file.write_text(body_text, encoding="utf-8")
    print(f"본문 저장: {body_file}")

    # 첨부파일 다운로드
    attachments = _download_attachments(service, message_id, msg["payload"], output_path)

    result = {
        "subject": subject,
        "from": sender,
        "date": date,
        "body_file": str(body_file),
        "attachments": attachments,
    }

    if attachments:
        print(f"\n첨부파일 {len(attachments)}개 저장:")
        for a in attachments:
            print(f"  - {a}")
    else:
        print("\n첨부파일 없음")

    return result


def _extract_body(payload: dict) -> str:
    """메일 본문(텍스트)을 추출합니다."""
    # 단일 파트
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # 멀티파트
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

    # text/plain이 없으면 text/html에서 추출
    for part in parts:
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            return html

    # 중첩 멀티파트
    for part in parts:
        if part.get("parts"):
            result = _extract_body(part)
            if result:
                return result

    return "(본문 없음)"


def _download_attachments(service, message_id: str, payload: dict, output_path: Path) -> list[str]:
    """첨부파일을 다운로드하여 저장합니다."""
    attachments = []
    parts = payload.get("parts", [])

    for part in parts:
        filename = part.get("filename")
        if not filename:
            # 중첩 파트 확인
            if part.get("parts"):
                attachments.extend(
                    _download_attachments(service, message_id, part, output_path)
                )
            continue

        attachment_id = part.get("body", {}).get("attachmentId")
        if not attachment_id:
            continue

        att = service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=attachment_id
        ).execute()

        data = base64.urlsafe_b64decode(att["data"])
        file_path = output_path / filename

        # 동일 파일명 충돌 방지
        counter = 1
        while file_path.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            file_path = output_path / f"{stem}_{counter}{suffix}"
            counter += 1

        file_path.write_bytes(data)
        attachments.append(str(file_path))

    return attachments


def main():
    parser = argparse.ArgumentParser(description="Gmail 메일 검색 및 첨부파일 다운로드")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # search 서브커맨드
    search_parser = subparsers.add_parser("search", help="메일 검색")
    search_parser.add_argument("query", help="검색 키워드")
    search_parser.add_argument("--limit", type=int, default=5, help="결과 수 (기본: 5)")

    # fetch 서브커맨드
    fetch_parser = subparsers.add_parser("fetch", help="메일 본문 + 첨부파일 다운로드")
    fetch_parser.add_argument("message_id", help="메일 ID")
    fetch_parser.add_argument("--output", default="/tmp/approval-draft/", help="저장 경로")

    args = parser.parse_args()

    if args.command == "search":
        search_mail(args.query, args.limit)
    elif args.command == "fetch":
        fetch_mail(args.message_id, args.output)


if __name__ == "__main__":
    main()
