"""
批量场景生成器
流水线: 指令 → BDDL(.bddl) → JSON(.json)

用法:
  # 模板模式批量（快速，无网络）
  python3 batch_generate.py -i data/instructions/unsafe_instructions.jsonl -n 100

  # API 模式批量（多样性高）
  python3 batch_generate.py -i data/instructions/unsafe_instructions.jsonl --use-api -n 50
"""

import argparse
import json
import os
import time
from pathlib import Path
from collections import Counter

from generate_scenario import (
    generate, generate_full, detect_category,
    save_bddl, save_scene_json, bddl_to_scene_json,
)


def load_instructions(file_path: str) -> list[dict]:
    instructions = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                instructions.append(item)
            except json.JSONDecodeError:
                instructions.append({"instruction": line, "category": "unsafe"})
    return instructions


def main():
    parser = argparse.ArgumentParser(description="批量场景生成器（BDDL + JSON）")
    parser.add_argument("--input", "-i", type=str, required=True)
    parser.add_argument("--output-bddl", type=str, default="data/bddl")
    parser.add_argument("--output-scene", type=str, default="data/scenes")
    parser.add_argument("--limit", "-n", type=int, default=None)
    parser.add_argument("--use-api", action="store_true")
    parser.add_argument("--api-key", type=str, default=None)
    parser.add_argument("--bddl-only", action="store_true",
                        help="仅生成 BDDL 文件")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("API_KEY")

    instructions = load_instructions(args.input)
    if args.limit:
        instructions = instructions[:args.limit]

    print(f"指令: {len(instructions)} 条")
    print(f"模式: {'API' if args.use_api else '模板匹配'}")
    print(f"BDDL 输出: {args.output_bddl}")
    print(f"JSON 输出: {args.output_scene}\n")

    stats = Counter()
    start_time = time.time()
    success, failed = 0, 0

    for i, item in enumerate(instructions):
        inst = item["instruction"]
        cat = item.get("category", "unsafe")
        if cat == "unsafe":
            cat = None
        scene_id = f"scene_{i:04d}"

        print(f"[{i+1}/{len(instructions)}] {inst[:55]}")

        try:
            # Step 1: 生成 BDDL
            bddl, category, score, source, _ = generate(
                inst, cat, args.use_api, api_key
            )
            bddl_path = save_bddl(bddl, args.output_bddl, scene_id)
            stats["bddl"] += 1

            if args.bddl_only:
                stats[category] += 1
                stats["total"] += 1
                success += 1
                print(f"  [✓] {bddl_path}")
                continue

            # Step 2: BDDL → JSON
            scene = bddl_to_scene_json(bddl, inst, category, scene_id)
            scene_path = save_scene_json(scene, args.output_scene, scene_id)
            stats[category] += 1
            stats["total"] += 1
            success += 1
            print(f"  [✓] BDDL+JSON ({len(scene['objects'])} 物体, {len(bddl)} 字符)")

        except Exception as e:
            failed += 1
            print(f"  [✗] 失败: {e}")

    elapsed = time.time() - start_time

    print(f"\n{'='*55}")
    print(f"完成! 成功: {success}  失败: {failed}")
    print(f"BDDL 文件: {stats.get('bddl', 0)}")
    print(f"JSON 场景: {stats.get('total', 0)}")
    if stats["total"] > 0:
        print(f"耗时: {elapsed:.1f}s (平均 {elapsed/stats['total']:.1f}s/场景)")
    print(f"\n类别分布:")
    for cat in ["malicious", "unauthorized", "physical_hazard", "environment"]:
        if stats[cat] > 0:
            print(f"  {cat}: {stats[cat]}")


if __name__ == "__main__":
    main()
