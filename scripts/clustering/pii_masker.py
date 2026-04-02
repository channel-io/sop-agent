"""
개인정보(PII) 마스킹 유틸리티.

저장 시점에 자동 적용되어 결과 파일에 개인정보가 남지 않도록 합니다.

마스킹 대상:
  - 전화번호: 01012345678 → 010****5678
  - 이메일: user@naver.com → u***r@naver.com
  - 내부 링크: desk.channel.io/... → ***masked***

사용:
  from scripts.clustering.pii_masker import mask_dataframe, mask_text

  df = mask_dataframe(df, columns=['plainText', 'summarizedMessage'])
  text = mask_text("연락처: 01012345678")
"""

import re

# ── 전화번호 ────────────────────────────────────────────────────────────── #

_PHONE_PATTERNS = [
    # 010-1234-5678 / 010.1234.5678
    (re.compile(r'(01[0-9])[-.](\d{3,4})[-.](\d{4})'), r'\1-****-\3'),
    # 01012345678 (11자리)
    (re.compile(r'(01[0-9])(\d{4})(\d{4})'), r'\1****\3'),
    # 821012345678 (국제번호)
    (re.compile(r'(82)(1[0-9])(\d{4})(\d{4})'), r'\1\2****\4'),
    # +821012345678
    (re.compile(r'(\+82)(1[0-9])(\d{4})(\d{4})'), r'\1\2****\4'),
]


def _mask_phones(text: str) -> str:
    for pattern, replacement in _PHONE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ── 이메일 ──────────────────────────────────────────────────────────────── #

_EMAIL_RE = re.compile(r'([a-zA-Z0-9._+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')

# 마스킹에서 제외할 플레이스홀더 도메인
_PLACEHOLDER_EMAILS = {'example.com', 'example.org', 'test.com'}
_PLACEHOLDER_LOCALS = {'new_email', 'email', 'test'}


def _mask_emails(text: str) -> str:
    def _replace(m):
        local, domain = m.group(1), m.group(2)
        # 플레이스홀더는 그대로
        if domain in _PLACEHOLDER_EMAILS or local in _PLACEHOLDER_LOCALS:
            return m.group(0)
        # 이미 마스킹된 경우
        if '***' in local:
            return m.group(0)
        if len(local) <= 2:
            return local[0] + '***@' + domain
        return local[0] + '***' + local[-1] + '@' + domain

    return _EMAIL_RE.sub(_replace, text)


# ── 내부 링크 ───────────────────────────────────────────────────────────── #

_INTERNAL_LINK_PATTERNS = [
    re.compile(r'https://desk\.channel\.io/[^\s"\')\]]+'),
    re.compile(r'https://[a-zA-Z0-9-]+\.slack\.com/[^\s"\')\]]+'),
    re.compile(r'https://[a-zA-Z0-9-]+\.atlassian\.net/[^\s"\')\]]+'),
]


def _mask_internal_links(text: str) -> str:
    for pattern in _INTERNAL_LINK_PATTERNS:
        text = pattern.sub('[내부링크 마스킹됨]', text)
    return text


# ── Public API ──────────────────────────────────────────────────────────── #

def mask_text(text) -> str:
    """단일 텍스트에 모든 PII 마스킹을 적용합니다."""
    if not isinstance(text, str):
        return text
    text = _mask_phones(text)
    text = _mask_emails(text)
    text = _mask_internal_links(text)
    return text


def mask_dataframe(df, columns=None):
    """
    DataFrame의 텍스트 컬럼에 PII 마스킹을 적용합니다.

    Args:
        df: pandas DataFrame
        columns: 마스킹할 컬럼 리스트. None이면 object 타입 컬럼 전체.

    Returns:
        마스킹된 DataFrame (원본을 변경하지 않고 복사본 반환)
    """
    df = df.copy()
    if columns is None:
        columns = [c for c in df.columns if df[c].dtype == 'object']

    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(mask_text)

    return df


def mask_json_str(json_str: str) -> str:
    """JSON 문자열 전체에 PII 마스킹을 적용합니다."""
    json_str = _mask_phones(json_str)
    json_str = _mask_emails(json_str)
    json_str = _mask_internal_links(json_str)
    return json_str
