import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    version_path = root / "app" / "version.json"
    build_dir = root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    version = ""
    try:
        with version_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            version = str(data.get("version", "")).strip()
    except Exception:
        version = ""

    exe_name = f"TradeLink Studio {version}" if version else "TradeLink Studio"

    version_file_content = f"""# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1,0,0,0),
        prodvers=(1,0,0,0),
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=(0,0)
        ),
    kids=[
        StringFileInfo([StringTable('040904b0',[
            StringStruct('CompanyName','Alexander Mishchenko'),
            StringStruct('FileDescription','TradeLink Studio'),
            StringStruct('FileVersion','{version}'),
            StringStruct('InternalName','{exe_name}'),
            StringStruct('OriginalFilename','{exe_name}.exe'),
            StringStruct('ProductName','TradeLink Studio'),
            StringStruct('ProductVersion','{version}')
        ])]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)
"""

    (build_dir / "version_file.txt").write_text(version_file_content, encoding="utf-8")
    (build_dir / "exe_name.txt").write_text(exe_name, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
