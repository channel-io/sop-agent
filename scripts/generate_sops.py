#!/usr/bin/env python3
"""
Stage 3-4 통합: SOP 문서 자동 생성 스크립트

입력:
  - results/assacom/02_extraction/patterns.json
  - results/assacom/assacom_messages.csv
  - templates/HT_template.md
  - templates/TS_template.md

출력:
  - results/assacom/04_sops/[HT_001].md ~ [HT_005].md
  - results/assacom/04_sops/[TS_001].md ~ [TS_005].md
"""

import json
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Upstage Solar API
from openai import OpenAI

# Request timeout (seconds) for LLM calls to avoid hanging requests
DEFAULT_LLM_TIMEOUT = 60

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import UPSTAGE_API_KEY, LLM_MODEL


class SOPGenerator:
    """SOP 문서 자동 생성기"""

    def __init__(self, patterns_path: str, messages_path: str, output_dir: str):
        self.patterns_path = patterns_path
        self.messages_path = messages_path
        self.output_dir = output_dir

        # API 클라이언트 (with request timeout)
        self.client = OpenAI(
            api_key=UPSTAGE_API_KEY,
            base_url="https://api.upstage.ai/v1/solar",
            timeout=DEFAULT_LLM_TIMEOUT
        )

        # 데이터 로드
        self.patterns_data = self._load_patterns()
        self.messages_df = self._load_messages()

        # 템플릿 로드
        self.ht_template = self._load_template("templates/HT_template.md")
        self.ts_template = self._load_template("templates/TS_template.md")

        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        print(f"✅ SOP Generator 초기화 완료")
        print(f"   - 클러스터: {len(self.patterns_data['clusters'])}개")
        print(f"   - 메시지: {len(self.messages_df)}개")

    def _load_patterns(self) -> Dict:
        """patterns.json 로드"""
        with open(self.patterns_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_messages(self) -> pd.DataFrame:
        """assacom_messages.csv 로드"""
        return pd.read_csv(self.messages_path)

    def _load_template(self, template_path: str) -> str:
        """템플릿 파일 로드"""
        with open(PROJECT_ROOT / template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_all_sops(self):
        """모든 SOP 문서 생성"""
        clusters = self.patterns_data['clusters']

        ht_count = 0
        ts_count = 0

        for cluster in clusters:
            cluster_id = cluster['cluster_id']
            sop_type = cluster['sop_type_recommendation']['type']

            if sop_type == 'HT':
                ht_count += 1
                sop_id = f"HT_{ht_count:03d}"
            else:
                ts_count += 1
                sop_id = f"TS_{ts_count:03d}"

            print(f"\n{'='*60}")
            print(f"🔄 [{sop_id}] 생성 중... (Cluster {cluster_id})")
            print(f"{'='*60}")

            sop_content = self.generate_sop(cluster, sop_id)

            # 파일명 생성 (슬래시 제거)
            label = cluster['label'].replace('/', '_')
            filename = f"[{sop_id}] {label}.md"
            output_path = os.path.join(self.output_dir, filename)

            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sop_content)

            print(f"✅ 저장 완료: {filename}")

        print(f"\n{'='*60}")
        print(f"✅ 전체 SOP 생성 완료!")
        print(f"   - HT: {ht_count}개")
        print(f"   - TS: {ts_count}개")
        print(f"   - 출력 경로: {self.output_dir}")
        print(f"{'='*60}")

    def generate_sop(self, cluster: Dict, sop_id: str) -> str:
        """단일 SOP 문서 생성"""

        sop_type = cluster['sop_type_recommendation']['type']
        cluster_id = cluster['cluster_id']

        # 1. 템플릿 선택
        template = self.ht_template if sop_type == 'HT' else self.ts_template

        # 2. 클러스터 메시지 필터링
        cluster_messages = self.messages_df[
            self.messages_df['cluster_id'] == cluster_id
        ]

        # 3. 톤앤매너 추출 (실제 대화에서)
        print(f"   📝 톤앤매너 추출 중...")
        tone_and_manner = self._extract_tone_and_manner(cluster_messages)

        # 4. LLM을 활용한 SOP 내용 생성
        print(f"   🤖 LLM으로 SOP 내용 생성 중...")
        sop_content = self._generate_sop_content_with_llm(
            cluster=cluster,
            sop_id=sop_id,
            sop_type=sop_type,
            template=template,
            tone_and_manner=tone_and_manner
        )

        return sop_content

    def _extract_tone_and_manner(self, cluster_messages: pd.DataFrame) -> Dict[str, List[str]]:
        """실제 대화에서 톤앤매너 추출"""

        # 상담원 메시지만 필터링
        manager_messages = cluster_messages[
            cluster_messages['personType'] == 'manager'
        ]['plainText'].dropna().tolist()

        if len(manager_messages) == 0:
            return {
                "greeting": ["안녕하세요, 고객님!"],
                "empathy": ["불편을 드려 죄송합니다"],
                "closing": ["감사합니다!"]
            }

        # 샘플 추출 (최대 20개)
        sample_messages = manager_messages[:20] if len(manager_messages) > 20 else manager_messages

        # LLM으로 톤앤매너 분석
        prompt = f"""다음은 실제 고객 상담 중 상담원이 사용한 메시지들입니다.
이 메시지들을 분석하여 톤앤매너를 추출해주세요.

**상담원 메시지 샘플:**
{chr(10).join([f"- {msg}" for msg in sample_messages[:10]])}

**요청사항:**
다음 JSON 형식으로 톤앤매너를 추출해주세요:

{{
  "greeting": ["인사 표현 1", "인사 표현 2"],
  "empathy": ["공감 표현 1", "공감 표현 2"],
  "closing": ["마무리 표현 1", "마무리 표현 2"],
  "avoid": ["피해야 할 표현 1", "피해야 할 표현 2"]
}}

**주의사항:**
- 실제 메시지에서 사용된 표현을 그대로 추출하세요
- 각 카테고리당 2-3개 예시만 추출
- 브랜드 톤 (Assacom: 최고의 품질과 합리적인 가격)을 반영
- JSON 형식만 반환하세요 (설명 불필요)
"""

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            result_text = response.choices[0].message.content.strip()

            # JSON 파싱
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            return json.loads(result_text)

        except Exception as e:
            print(f"   ⚠️  톤앤매너 추출 실패: {e}")
            return {
                "greeting": ["안녕하세요, 고객님!"],
                "empathy": ["불편을 드려 죄송합니다"],
                "closing": ["감사합니다!"]
            }

    def _generate_sop_content_with_llm(
        self,
        cluster: Dict,
        sop_id: str,
        sop_type: str,
        template: str,
        tone_and_manner: Dict
    ) -> str:
        """LLM을 활용하여 SOP 내용 생성"""

        # 클러스터 정보 요약
        cluster_summary = {
            "cluster_id": cluster['cluster_id'],
            "label": cluster['label'],
            "category": cluster['category'],
            "size": cluster['cluster_size'],
            "patterns": cluster['patterns'][:10],  # 상위 10개 패턴만
            "faq_pairs": cluster['faq_pairs'][:5],  # 상위 5개 FAQ만
            "response_strategy": cluster['response_strategy']
        }

        prompt = f"""당신은 고객 상담 SOP 문서를 작성하는 전문가입니다.
아래 데이터를 바탕으로 실용적이고 구체적인 SOP 문서를 작성해주세요.

# 입력 데이터

## SOP 정보
- SOP ID: [{sop_id}]
- SOP 타입: {sop_type} ({'How-To (정보 제공/안내)' if sop_type == 'HT' else 'Troubleshooting (문제 해결)'})
- 생성일: {datetime.now().strftime('%Y-%m-%d')}

## 클러스터 분석 결과
```json
{json.dumps(cluster_summary, ensure_ascii=False, indent=2)}
```

## 추출된 톤앤매너
```json
{json.dumps(tone_and_manner, ensure_ascii=False, indent=2)}
```

# 템플릿
```markdown
{template}
```

# 작성 지침

1. **목적 섹션**: 이 SOP가 다루는 주제와 적용 범위를 명확히 정의
2. **주의사항**: 응대 시 반드시 유의해야 할 점과 강조 사항
3. **{'내용' if sop_type == 'HT' else '문제 해결 프로세스'}**:
   - patterns 데이터를 기반으로 케이스 구성
   - 각 케이스마다 구체적인 응대 방법과 응답 예시 제공
   - FAQ 데이터를 케이스에 자연스럽게 통합
4. **톤앤매너**: 추출된 톤앤매너를 실제 사용 가능한 형태로 정리
5. **에스컬레이션**: response_strategy의 escalation_target을 기반으로 작성
6. **데이터 분석 정보**: 클러스터 정보를 YAML 형식으로 정리

# 주의사항

- ❌ 추측하지 마세요 - 데이터에 있는 내용만 사용
- ✅ 실제 사용 가능한 응답 예시 포함
- ✅ 구체적이고 액션 지향적으로 작성
- ✅ 템플릿 구조를 그대로 따르되, (예시) 부분은 실제 내용으로 채우기
- ✅ 한국어로 작성 (브랜드: Assacom)

# 출력

완성된 SOP 문서를 마크다운 형식으로 작성해주세요.
"""

        try:
            print(f"   🤖 LLM 호출 중... (모델: {LLM_MODEL})")

            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=8000
            )

            sop_content = response.choices[0].message.content.strip()

            # 마크다운 코드 블록 제거
            if sop_content.startswith("```markdown"):
                sop_content = sop_content[len("```markdown"):].strip()
            if sop_content.startswith("```"):
                sop_content = sop_content[3:].strip()
            if sop_content.endswith("```"):
                sop_content = sop_content[:-3].strip()

            return sop_content

        except Exception as e:
            print(f"   ❌ LLM 호출 실패: {e}")
            raise


def main():
    """메인 실행 함수"""

    # 경로 설정 (절대 경로)
    base_dir = PROJECT_ROOT
    patterns_path = base_dir / "results/assacom/02_extraction/patterns.json"
    messages_path = base_dir / "results/assacom/assacom_messages.csv"
    output_dir = base_dir / "results/assacom/04_sops"

    print("="*60)
    print("🚀 Stage 3-4 통합: SOP 자동 생성 시작")
    print("="*60)
    print(f"입력:")
    print(f"  - {patterns_path}")
    print(f"  - {messages_path}")
    print(f"출력:")
    print(f"  - {output_dir}/")
    print("="*60)

    # Generator 초기화
    generator = SOPGenerator(
        patterns_path=str(patterns_path),
        messages_path=str(messages_path),
        output_dir=str(output_dir)
    )

    # 전체 SOP 생성
    generator.generate_all_sops()

    print("\n✅ 작업 완료!")


if __name__ == "__main__":
    main()
