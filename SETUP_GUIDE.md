# 설치 가이드

Excel 고객 상담 데이터를 Agent SOP 문서 + 플로우차트로 자동 변환하는 AI 파이프라인 설치 가이드입니다.

---

## 사전 준비

1. **Claude Code 설치** — https://claude.ai/code
2. **Upstage API 키 발급** — DM 주시면 전달드리겠습니다!

---

## 설치 방법

```bash
# 1. 설치 스크립트 실행 (Python 가상환경 + 패키지 자동 설치)
chmod +x setup.sh
./setup.sh

# 2. API 키 입력
# .env 파일에 UPSTAGE_API_KEY 입력
```

---

## 실행 방법

`data/` 폴더에 고객 상담 Excel 파일을 넣고, 해당 폴더를 Claude Code로 연 뒤 명령어 실행:

```
/userchat-to-sop-pipeline    # SOP 문서 + 플로우차트 생성 (약 15~30분)
```

단계별로 실행하려면:

```
/stage1-clustering              # 클러스터링
/stage2-extraction              # 패턴 추출
/stage3-sop-generation          # SOP 문서 생성
/stage4-flowchart-generation    # 플로우차트 생성
(미완성X) /stage5-sales-report            # ROI 세일즈 리포트 생성
```

---

## 문제 해결

### "pip3: command not found"

```bash
python3 -m ensurepip --upgrade
```

### "Permission denied" 또는 "Externally managed environment"

```bash
# 가상환경 사용 (권장)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "ImportError: No module named 'pandas'"

```bash
pip3 install pandas numpy scikit-learn openpyxl openai tqdm --user
```

### 그 외 에러

에러 메시지를 Claude Code에 붙여넣으면 자동으로 해결책을 제시합니다.

---

## Stage 4 플로우차트 SVG 생성 (선택)

Mermaid CLI가 없어도 마크다운 파일은 생성됩니다. SVG 이미지가 필요한 경우에만 설치하세요.

```bash
# Node.js 설치 확인
node --version

# Mermaid CLI 설치
npm install -g @mermaid-js/mermaid-cli

# SVG 변환
mmdc -i FLOWCHART.md -o flowchart.svg -b transparent
```
