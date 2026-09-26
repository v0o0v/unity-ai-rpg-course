#!/usr/bin/env python3
"""Pack equal-size PNG frames without trimming or changing pivots.

Install: python -m pip install Pillow
Example:
  python tools/pack_frames.py ArtSources/Clean/hero_walk_S \
    --output ArtSources/Packed/hero_walk_S.png --columns 6 --cell 64 \
    --pivot 0.5 0.125

Input files are never modified. JSON frame coordinates use a top-left origin;
pivot coordinates are normalized with a bottom-left origin (Unity convention).
This is an offline helper, not a Unity importer or animation correctness checker.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from PIL import Image


def natural_key(path: Path) -> list:
    return [int(s) if s.isdigit() else s.casefold()
            for s in re.split(r"(\d+)", path.name)]


def pack_frames(input_dir: Path, output: Path, *, columns: int = 6,
                cell: int = 64, pivot: tuple[float, float] = (0.5, 0.125),
                fps: float = 12.0, allow_empty: bool = False,
                force: bool = False) -> dict:
    input_dir, output = input_dir.resolve(), output.resolve()
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    if output.suffix.lower() != '.png':
        raise ValueError('Output must end in .png')
    if columns < 1 or columns > 256 or cell < 1 or cell > 4096:
        raise ValueError('Use columns 1..256 and cell 1..4096')
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('fps must be a positive finite number')
    if len(pivot) != 2 or not all(math.isfinite(v) and 0 <= v <= 1 for v in pivot):
        raise ValueError('Both pivot coordinates must be within 0..1')
    # Keep exports out of the input folder to avoid reading an old sheet as a frame.
    if output.parent == input_dir:
        raise ValueError('Output must be outside the input frame directory')
    json_path = output.with_suffix('.json')
    if not force and (output.exists() or json_path.exists()):
        raise ValueError('Output already exists. Use a new name or explicitly add --force.')
    files = sorted((p for p in input_dir.iterdir()
                    if p.is_file() and p.suffix.lower() == '.png'), key=natural_key)
    if not files:
        raise ValueError('No PNG frames found in the input directory')
    rows = math.ceil(len(files) / columns)
    width, height = columns * cell, rows * cell
    if width * height > 64_000_000:
        raise ValueError('Sheet exceeds the helper\'s 64-million-pixel safety limit')
    sheet = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    frames = []
    warnings = []
    seen_hashes: dict[str, str] = {}
    for i, source in enumerate(files):
        with Image.open(source) as original:
            if original.size != (cell, cell):
                raise ValueError(f'{source.name}: expected {cell}x{cell}, got {original.size}')
            frame = original.convert('RGBA')
            alpha = frame.getchannel('A')
            alpha_min, alpha_max = alpha.getextrema()
            if alpha_max == 0 and not allow_empty:
                raise ValueError(f'{source.name}: fully transparent; use --allow-empty for intentional blank frames')
            if alpha_min == 255:
                warnings.append(f'{source.name}: fully opaque; check that a background is intended')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            pixel_digest = hashlib.sha256(frame.tobytes()).hexdigest()
            if pixel_digest in seen_hashes:
                warnings.append(f'{source.name}: same pixels as {seen_hashes[pixel_digest]}; verify the pose')
            seen_hashes[pixel_digest] = source.name
            x, y = (i % columns) * cell, (i // columns) * cell
            # No mask: copy RGBA exactly; alpha must not be multiplied twice.
            sheet.paste(frame, (x, y))
            frames.append({
                'index': i, 'source': source.name, 'sourceSha256': digest,
                'rectTopLeft': {'x': x, 'y': y, 'width': cell, 'height': cell},
                'pivotNormalizedBottomLeft': {'x': pivot[0], 'y': pivot[1]},
                'durationSeconds': 1.0 / fps,
                'alphaRange': [alpha_min, alpha_max],
            })
    meta = {
        'format': 'ashfall.fixed-cell-spritesheet', 'formatVersion': 1,
        'sheet': output.name, 'size': {'width': width, 'height': height},
        'cellSize': cell, 'columns': columns, 'rows': rows,
        'frameCount': len(frames), 'fps': fps, 'trimmed': False, 'rotated': False,
        'rectOrigin': 'top-left', 'pivotOrigin': 'bottom-left-normalized',
        'frames': frames, 'warnings': warnings,
        'note': 'Unity must invert rectangle Y as sheetHeight - y - height. This does not certify animation quality.'
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format='PNG')
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input_dir', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--columns', type=int, default=6)
    parser.add_argument('--cell', type=int, default=64)
    parser.add_argument('--pivot', type=float, nargs=2, default=(0.5, 0.125), metavar=('X', 'Y'))
    parser.add_argument('--fps', type=float, default=12.0)
    parser.add_argument('--allow-empty', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        meta = pack_frames(args.input_dir, args.output, columns=args.columns,
                           cell=args.cell, pivot=tuple(args.pivot), fps=args.fps,
                           allow_empty=args.allow_empty, force=args.force)
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Packed {meta["frameCount"]} frames -> {args.output}')
    print(f'Metadata -> {args.output.with_suffix(".json")}')
    for warning in meta['warnings']:
        print(f'WARNING: {warning}', file=sys.stderr)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
