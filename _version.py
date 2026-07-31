"""애플리케이션 버전과 실행 파일 메타데이터의 단일 소스.

버전을 올릴 때는 이 파일의 ``__version__`` 하나만 수정합니다.

- ``main.py``는 이 값을 읽어 ``APP_VERSION``을 만듭니다.
- ``tools/make_version_file.py``가 이 값으로 PyInstaller용 ``version.txt``를
  생성합니다.
- 릴리스 워크플로가 푸시된 git 태그와 이 값이 일치하는지 검사하고,
  다르면 빌드를 실패시킵니다.

따라서 태그, 실행 파일 메타데이터, 앱이 보고하는 버전이 어긋날 수 없습니다.
"""

__version__ = "1.1.3"

COMPANY_NAME = "Mongle Studio"
PRODUCT_NAME = "몽글몽글 메모 스티커"
FILE_DESCRIPTION = "몽글몽글 메모 스티커"
INTERNAL_NAME = "MongleSticker"
ORIGINAL_FILENAME = "몽글몽글 스티커.exe"
LEGAL_COPYRIGHT = "Copyright (C) 2026. All rights reserved."
