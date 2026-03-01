from pathlib import Path

# Tiny helper script to "clean up" map files in assets/maps.
#
# Why it exists:
# - Our GridWorld loader expects maps to be rectangular (every row same length).
# - When editing maps by hand, it's easy to accidentally add/remove a character on one line.
#
# What this tool does:
# - Finds the most common row width in the file.
# - Any line that doesn't match gets auto-fixed:
#   - too long  -> truncated
#   - too short -> padded (with 'F')
#
# Note: this script rewrites files, so run it intentionally.
MAPS_DIR = Path(__file__).resolve().parents[1] / "assets" / "maps"

def fix_one(path: Path) -> None:
    # Read the map as raw text lines.
    raw = path.read_text(encoding="utf-8").splitlines()

    # Remove empty lines and strip trailing whitespace.
    # (This is meant for older maps that had stray whitespace; newer weighted maps may
    # intentionally include spaces as tiles, so be careful when using this.)
    lines = [ln.rstrip() for ln in raw if ln.strip() != ""]
    if not lines:
        print(f"[SKIP] {path.name}: empty")
        return

    widths = [len(ln) for ln in lines]
    # Pick the width that appears most often.
    # This helps us guess the "intended" width of the map.
    target = max(set(widths), key=widths.count)  # most common width

    bad = [(i, widths[i], lines[i]) for i in range(len(lines)) if widths[i] != target]
    if bad:
        print(f"[BAD] {path.name}: target={target}, widths={sorted(set(widths))}")
        for i, w, row in bad[:8]:
            print(f"  line {i+1}: len={w} row={row!r}")

        # Auto-fix: truncate if too long, pad with 'F' if too short
        fixed = []
        for ln in lines:
            if len(ln) > target:
                fixed.append(ln[:target])
            else:
                fixed.append(ln.ljust(target, "F"))

        path.write_text("\n".join(fixed) + "\n", encoding="utf-8")
        print(f"      -> fixed {path.name}\n")
    else:
        print(f"[OK]  {path.name} ({target} cols, {len(lines)} rows)")

def main():
    # Run the fixer across every .txt map file.
    if not MAPS_DIR.exists():
        raise FileNotFoundError(f"Maps dir not found: {MAPS_DIR}")
    for p in sorted(MAPS_DIR.glob("*.txt")):
        fix_one(p)

if __name__ == "__main__":
    main()