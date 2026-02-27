from pathlib import Path

MAPS_DIR = Path(__file__).resolve().parents[1] / "assets" / "maps"

def fix_one(path: Path) -> None:
    raw = path.read_text(encoding="utf-8").splitlines()

    # remove empty lines, strip trailing whitespace
    lines = [ln.rstrip() for ln in raw if ln.strip() != ""]
    if not lines:
        print(f"[SKIP] {path.name}: empty")
        return

    widths = [len(ln) for ln in lines]
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
    if not MAPS_DIR.exists():
        raise FileNotFoundError(f"Maps dir not found: {MAPS_DIR}")
    for p in sorted(MAPS_DIR.glob("*.txt")):
        fix_one(p)

if __name__ == "__main__":
    main()