"""Segmented final render to avoid ENOSPC on long keeps."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agentic_editor.compose import (
    _clear_remotion_cache,
    _remotion_cli,
    _remotion_env,
    cleanup_remotion_after_final,
    prepare_compose,
    remotion_kit_dir,
    remotion_render_accel_args,
)


def main() -> int:
    episode = Path(sys.argv[1]).resolve()
    props = episode / "edit" / "remotion-props.json"
    out = episode / "edit" / "final.mp4"
    parts_dir = episode / "edit" / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    prepare_compose(episode, verbose=True)
    data = __import__("json").loads(props.read_text(encoding="utf-8"))
    total = int(data["timeline"]["durationInFrames"])
    kit = remotion_kit_dir()
    env = _remotion_env()
    env["AE_TIMELINE_PROPS"] = str(props)
    env["AE_EPISODE"] = str(episode)
    accel = remotion_render_accel_args(nvenc=False, verbose=True)

    # ~3 equal segments
    n = 3
    chunk = (total + n - 1) // n
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < total:
        end = min(total - 1, start + chunk - 1)
        ranges.append((start, end))
        start = end + 1

    part_files: list[Path] = []
    for i, (a, b) in enumerate(ranges, 1):
        part = parts_dir / f"part-{i:02d}.mp4"
        part_files.append(part)
        cmd = [
            *_remotion_cli(kit),
            "render",
            "src/index.ts",
            "AgenticTimeline",
            str(part),
            "--props",
            str(props),
            f"--frames={a}-{b}",
            "--concurrency=2",
            "--jpeg-quality=80",
            *accel,
        ]
        print(f"\n=== Segment {i}/{len(ranges)} frames {a}-{b} ===")
        print(f"$ cd {kit} && {' '.join(cmd)}")
        subprocess.run(cmd, cwd=str(kit), env=env, check=True)
        _clear_remotion_cache()

    list_file = parts_dir / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in part_files) + "\n",
        encoding="utf-8",
    )
    concat_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(out),
    ]
    print(f"\n=== Concat → {out} ===")
    subprocess.run(concat_cmd, check=True)
    cleanup_remotion_after_final(verbose=True)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
