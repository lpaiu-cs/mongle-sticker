"""``_version.py``로부터 PyInstaller용 ``version.txt``를 생성합니다.

``version.txt``는 생성물이므로 git으로 추적하지 않습니다. 빌드 전에 실행하세요.

    python tools/make_version_file.py

``--check`` 옵션을 주면 파일을 쓰지 않고, 기존 ``version.txt``가 현재 버전과
일치하는지만 검사합니다(불일치 시 종료 코드 1).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import _version  # noqa: E402  (경로 설정 이후에 import해야 함)

OUTPUT_PATH = REPO_ROOT / "version.txt"

# 041204b0 = 한국어(1042) + Unicode(1200)
LANGUAGE_CODEPAGE = "041204b0"
TRANSLATION = [1042, 1200]

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '{language_codepage}',
        [StringStruct('CompanyName', '{company_name}'),
        StringStruct('FileDescription', '{file_description}'),
        StringStruct('FileVersion', '{version}'),
        StringStruct('InternalName', '{internal_name}'),
        StringStruct('LegalCopyright', '{legal_copyright}'),
        StringStruct('OriginalFilename', '{original_filename}'),
        StringStruct('ProductName', '{product_name}'),
        StringStruct('ProductVersion', '{version}')])
      ]),
    VarFileInfo([VarStruct('Translation', {translation})])
  ]
)
"""


def version_tuple(version: str) -> tuple[int, int, int, int]:
    """'1.1.3' 같은 문자열을 Windows가 요구하는 4자리 정수 튜플로 변환합니다."""
    parts = version.split(".")
    if not 1 <= len(parts) <= 4:
        raise ValueError(f"Unsupported version format: {version!r}")

    try:
        numbers = [int(part) for part in parts]
    except ValueError as error:
        raise ValueError(f"Version must contain only integers: {version!r}") from error

    if any(number < 0 or number > 65535 for number in numbers):
        raise ValueError(f"Each version field must fit in 16 bits: {version!r}")

    numbers += [0] * (4 - len(numbers))
    return tuple(numbers)  # type: ignore[return-value]


def render() -> str:
    for field in ("COMPANY_NAME", "PRODUCT_NAME", "FILE_DESCRIPTION",
                  "INTERNAL_NAME", "ORIGINAL_FILENAME", "LEGAL_COPYRIGHT"):
        value = getattr(_version, field)
        if "'" in value:
            raise ValueError(f"{field} must not contain a single quote: {value!r}")

    return TEMPLATE.format(
        version=_version.__version__,
        version_tuple=version_tuple(_version.__version__),
        language_codepage=LANGUAGE_CODEPAGE,
        translation=TRANSLATION,
        company_name=_version.COMPANY_NAME,
        file_description=_version.FILE_DESCRIPTION,
        internal_name=_version.INTERNAL_NAME,
        legal_copyright=_version.LEGAL_COPYRIGHT,
        original_filename=_version.ORIGINAL_FILENAME,
        product_name=_version.PRODUCT_NAME,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="파일을 쓰지 않고 기존 version.txt가 최신인지만 확인합니다.",
    )
    arguments = parser.parse_args()

    expected = render()

    if arguments.check:
        if not OUTPUT_PATH.exists():
            print(f"version.txt가 없습니다: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        actual = OUTPUT_PATH.read_text(encoding="utf-8")
        if actual != expected:
            print(
                "version.txt가 _version.py와 일치하지 않습니다. "
                "python tools/make_version_file.py 를 실행하세요.",
                file=sys.stderr,
            )
            return 1
        print(f"version.txt는 최신입니다 (v{_version.__version__}).")
        return 0

    # PyInstaller는 버전 리소스 파일을 BOM 없는 UTF-8로 읽습니다.
    OUTPUT_PATH.write_text(expected, encoding="utf-8", newline="\n")
    print(f"{OUTPUT_PATH} 생성 완료 (v{_version.__version__}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
