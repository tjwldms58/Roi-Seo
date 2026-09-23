# 힐마루케어 레포트

엑셀을 올리면 PDF 레포트를 만듭니다. 프로그램은 두 개입니다.

- 수면 레포트: 웨어러블 7일 데이터로 불면 중심 수면 리듬 리포트를 만듭니다.
- 종합 레포트: 방문 건강관리 회차 양식으로 회복 관리 리포트를 만듭니다.

계산식과 문장은 코드에 없습니다. 수면은 `sleep_report/logic/sleep_logic.xlsx`의 수식을, 종합은 `recovery_report/logic/recovery_template.xlsx`의 수식을 LibreOffice가 다시 계산합니다. 엑셀만 교체하면 수치와 문장이 바뀝니다.

섹션을 언제 빼 낼지는 각 프로그램의 `rules.yaml`에 있습니다. 핵심 입력이 전부 비어 있으면 그 섹션은 PDF에서 빠지고, 일부만 있으면 있는 값으로 그리거나 `해당 데이터 없음`을 표시합니다. PDF 하단과 마지막 장에 로직 버전, 채워진 항목 수, 생략된 섹션이 나옵니다. `0`은 빈 값이 아닙니다.

## 실행

```bash
pip install -r requirements.txt
sudo apt install libreoffice-calc
python -m sleep_report
python -m recovery_report
```

수면 화면은 http://127.0.0.1:8081 , 종합 화면은 http://127.0.0.1:8082 입니다. 각 화면의 `샘플 레포트 보기`를 누르면 브라우저에서 레포트가 열립니다. 서버 없이 보려면 `preview/index.html` 을 브라우저로 여세요. 화면에서 각 페이지는 A4(210mm × 297mm)입니다.

## 수면 레포트에서 고치는 곳

- `S1_Input_Raw`, `S2_Input_Profile`: 대상자 입력
- `S3_Config`: 참고범위와 목표. 노란 칸
- `S6_Text_Gen`: 페이지 문장 수식
- `sleep_report/rules.yaml`: 페이지를 생략하는 기준, 버전, 수정일, 없음 문구

하루는 취침시각, 기상시각, 깊은수면이 모두 있을 때만 계산에 넣습니다. 각성시간 실측이 없으면 `06+` 페이지는 생략됩니다.

## 종합 레포트에서 고치는 곳

노란 칸이 입력입니다. 파란 칸은 수식입니다. 운동별 이전/이후가 하나도 없으면 그 페이지는 생략됩니다. 팔둘레와 어깨 가동범위가 모두 없으면 암종 페이지도 생략됩니다.

생략 기준과 버전은 `recovery_report/rules.yaml`에 있습니다.

## 테스트

```bash
python -m pytest
```
