"""把分章 Markdown 合并成便于连续阅读的全书。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "书稿"
OUTPUT = CHAPTERS / "全书.md"

parts = []
for number in range(18):
    matches = sorted(CHAPTERS.glob(f"{number:02d}-*.md"))
    if len(matches) != 1:
        raise RuntimeError(f"编号 {number:02d} 应恰好对应一个书稿文件")
    parts.append(matches[0].read_text(encoding="utf-8").strip())

header = "<!-- 由 scripts/build_book.py 生成；请修改书稿目录中的分章文件。 -->"
OUTPUT.write_text(header + "\n\n" + "\n\n".join(parts) + "\n", encoding="utf-8")
print(OUTPUT)
