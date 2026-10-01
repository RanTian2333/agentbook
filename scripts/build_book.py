"""把分章 Markdown 合并成便于连续阅读的全书。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "书稿"
OUTPUT = CHAPTERS / "全书.md"

chapters = sorted(CHAPTERS.glob("[0-9][0-9]-*.md"))
if not chapters:
    raise RuntimeError("未找到编号书稿")

parts = []
for number, chapter in enumerate(chapters):
    if chapter.name[:2] != f"{number:02d}":
        raise RuntimeError(f"编号 {number:02d} 缺失或重复")
    parts.append(chapter.read_text(encoding="utf-8").strip())

header = "<!-- 由 scripts/build_book.py 生成；请修改书稿目录中的分章文件。 -->"
OUTPUT.write_text(header + "\n\n" + "\n\n".join(parts) + "\n", encoding="utf-8")
print(OUTPUT)
