# 몽글몽글 바탕화면 메모 스티커 🌸

외부 텍스트 파일을 Windows 바탕화면 스티커로 표시하는 PyQt6 애플리케이션입니다. 원본 파일을 직접 편집하면 스티커 내용이 자동으로 갱신되며, 여러 파일을 서로 다른 스티커로 관리할 수 있습니다.

## 주요 기능

- 여러 `.txt` 파일을 각각 독립된 스티커로 표시
- 원본 파일 저장 시 내용 자동 갱신
- 스티커별 색상, 투명도, 글꼴, 글자 크기 설정
- 전체 또는 특정 줄 표시 (`all`, `3`, `1-5`, `3-`)
- Markdown 렌더링 선택
- 스티커 위치와 크기 저장
- 기본적으로 다른 창 아래에 배치하고, 핀 버튼으로 항상 위에 고정
- `Ctrl+Alt+M`으로 모든 스티커 숨김/복원
- Windows 시작 시 자동 실행 설정
- 시스템 트레이에서 스티커 관리 및 종료
- GitHub Releases를 통한 새 버전 알림

스티커는 클릭 가능한 창입니다. 텍스트 선택·복사와 핀 버튼 사용이 가능하며, 마우스 입력이 바탕화면으로 통과하지는 않습니다.

## 사용 방법

1. 앱을 실행하면 시스템 트레이에 핑크색 스티커 아이콘이 나타납니다.
2. 트레이 아이콘을 우클릭하고 **⚙️ 스티커 관리 / 크기 조절**을 선택합니다.
3. **➕ 새 스티커 바탕화면에 추가**를 눌러 연결할 텍스트 파일을 선택합니다.
4. 설정창이 열린 동안 스티커를 드래그하거나 우측 하단을 잡아 크기를 조절합니다.
5. 각 스티커의 **⚙️ 상세**에서 색상, 투명도, 표시할 줄, 글꼴과 Markdown 사용 여부를 설정합니다.
6. **✅ 설정 완료 및 모두 저장**을 눌러 편집 모드를 종료합니다.
7. 실제 내용은 **📝 열기**로 원본 파일을 편집한 뒤 저장합니다.

설정과 기본 메모는 다음 사용자 전용 경로에 저장됩니다.

```text
%LOCALAPPDATA%\MongleSticker\
├── config.json
├── memo.txt
└── mongle-sticker.log
```

설정 저장 실패, 파일 읽기 오류, 업데이트 확인 실패 등의 진단 정보는 `mongle-sticker.log`에서 확인할 수 있습니다. 손상된 설정 파일은 가능한 경우 `config.json.corrupt`로 보존됩니다.

## 개발 환경

- Windows
- Python 3.11+
- PyQt6
- PyInstaller

의존성 버전은 `requirements.txt`에 고정되어 있습니다. CI도 같은 파일을 사용합니다.

### 소스 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

### 실행 파일 빌드

`version.txt`는 `_version.py`에서 생성되는 파일이므로 빌드 전에 한 번 만들어야 합니다.

```powershell
python -m pip install -r requirements.txt
python tools/make_version_file.py
pyinstaller --clean --noconsole --onefile --icon=icon.ico --version-file version.txt --name "몽글몽글 스티커" main.py
```

빌드 결과는 `dist\몽글몽글 스티커.exe`에 생성됩니다.

## 버전 관리

버전의 유일한 소스는 `_version.py`의 `__version__`입니다.

| 대상 | 값을 얻는 방법 |
| --- | --- |
| 앱이 보고하는 버전 (`APP_VERSION`) | `main.py`가 `_version.py`에서 읽음 |
| 실행 파일 속성의 버전 (`version.txt`) | `tools/make_version_file.py`가 생성 |
| git 태그 | 릴리스 시 `v` + `__version__` 형식으로 생성 |

`tools/make_version_file.py --check`로 생성된 `version.txt`가 최신인지 확인할 수 있습니다.

## 릴리스

1. `_version.py`의 `__version__`을 올리고 커밋합니다.
2. 같은 값으로 태그를 만들어 푸시합니다. 예: `__version__ = "1.1.3"` → `git tag v1.1.3`
3. `git push origin main --follow-tags`

`v`로 시작하는 태그가 푸시되면 `.github/workflows/release.yml`이 Windows 실행 파일을 빌드해 GitHub Release에 업로드합니다. 워크플로는 빌드 전에 태그와 `_version.py`가 일치하는지 검사하고, 어긋나면 실패합니다. 따라서 버전이 맞지 않는 릴리스는 발행되지 않습니다.
