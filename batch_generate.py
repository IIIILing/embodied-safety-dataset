"""
批量场景生成器
从指令文件读取多条有害指令，批量生成场景 JSON
"""

import argparse
import json
import time
from pathlib import Path
from collections import Counter

# TODO: 接入 generate_scenario 模块
# from generate_scenario import generate_bddl, bddl_to_scene_json, save_scene


def load_instructions(file_path: str) -> list[dict]:
    """加载指令文件（每行一个 JSON 或纯文本）"""
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
    parser = argparse.ArgumentParser(description="批量场景生成器")
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="指令文件路径（每行一条指令）")
    parser.add_argument("--output", "-o", type=str, default="data/scenes",
                        help="场景输出目录")
    parser.add_argument("--limit", "-n", type=int, default=None,
                        help="限制生成数量")
    args = parser.parse_args()

    instructions = load_instructions(args.input)
    if args.limit:
        instructions = instructions[:args.limit]

    print(f"加载 {len(instructions)} 条指令")
    print(f"输出目录: {args.output}\n")

    stats = Counter()
    start_time = time.time()

    for i, item in enumerate(instructions):
        inst = item["instruction"]
        cat = item.get("category", "unsafe")
        scene_id = f"scene_{i:04d}"

        print(f"[{i+1}/{len(instructions)}] {inst[:50]}...")

        # TODO: 调用生成流程
        # bddl = generate_bddl(inst)
        # scene = bddl_to_scene_json(bddl, inst, cat)
        # save_scene(scene, args.output, scene_id)

        stats[cat] += 1
        stats["total"] += 1

    elapsed = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"生成完成!")
    print(f"总计: {stats['total']} 个场景")
    print(f"耗时: {elapsed:.1f}s (平均 {elapsed/stats['total']:.1f}s/场景)")
    print(f"\n按类别分布:")
    for cat in ["malicious", "unauthorized", "physical_hazard", "environment"]:
        if stats[cat] > 0:
            print(f"  {cat}: {stats[cat]}")


if __name__ == "__main__":
    main()
