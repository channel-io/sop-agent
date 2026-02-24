#!/bin/bash
# SOP Agent 설치 스크립트

set -e

echo "=========================================="
echo "  Userchat-to-SOP Pipeline 설치"
echo "=========================================="
echo ""

# Python 버전 확인
echo "[1/4] Python 확인 중..."
if ! command -v python3 &>/dev/null; then
  echo "  ❌ Python 3이 설치되어 있지 않습니다."
  echo "  https://www.python.org/downloads/ 에서 Python 3.9 이상을 설치해주세요."
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
  echo "  ❌ Python 3.9 이상이 필요합니다. (현재: $PYTHON_VERSION)"
  exit 1
fi

echo "  ✅ Python $PYTHON_VERSION"

# 가상환경 생성 (선택)
echo ""
echo "[2/4] 가상환경 설정..."
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "  ✅ 가상환경 생성: venv/"
else
  echo "  ✅ 기존 가상환경 사용: venv/"
fi

source venv/bin/activate

# 패키지 설치
echo ""
echo "[3/4] 패키지 설치 중..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✅ 패키지 설치 완료"

# .env 파일 설정
echo ""
echo "[4/4] 환경 변수 설정..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  ⚠️  .env 파일이 생성되었습니다."
  echo "  👉 .env 파일을 열어 UPSTAGE_API_KEY를 입력해주세요."
  echo "     발급: https://console.upstage.ai"
else
  echo "  ✅ .env 파일 존재"
fi

# 필요 디렉토리 생성
mkdir -p data results cache

echo ""
echo "=========================================="
echo "  설치 완료! 🎉"
echo "=========================================="
echo ""
echo "  다음 단계:"
echo "  1. .env 파일에 UPSTAGE_API_KEY 입력"
echo "  2. data/ 폴더에 고객 상담 Excel 파일 넣기"
echo "  3. Claude Code에서 폴더 열기"
echo "  4. /userchat-to-sop-pipeline 실행"
echo ""
echo "  가상환경 활성화 (다음 실행 시):"
echo "  source venv/bin/activate"
echo ""
