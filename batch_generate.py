"""
批量场景生成器
从指令文件读取多条有害指令，批量生成场景 JSON
"""

import argparse
import json
import time
from pathlib import Path
from collections import Counter

from generate_scenario import generate_scenario, save_scene, detect_category


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
    parser.add_argument("--use-api", action="store_true",
                        help="使用 DeepSeek API 生成")
    parser.add_argument("--api-key", type=str, default=None,
                        help="DeepSeek API Key")
    args = parser.parse_args()

    instructions = load_instructions(args.input)
    if args.limit:
        instructions = instructions[:args.limit]

    print(f"加载 {len(instructions)} 条指令")
    print(f"输出目录: {args.output}")
    print(f"生成模式: {'API (DeepSeek)' if args.use_api else '模板匹配'}\n")

    stats = Counter()
    start_time = time.time()

    for i, item in enumerate(instructions):
        inst = item["instruction"]
        cat = item.get("category", "unsafe")
        scene_id = f"scene_{i:04d}"

        print(f"[{i+1}/{len(instructions)}] {inst[:50]}...")

        try:
            scene, score, matched, mode = generate_scenario(
                inst, cat if cat != "unsafe" else None,
                use_api=args.use_api, api_key=args.api_key
            )
            save_scene(scene, args.output, scene_id)
            stats[scene["category"]] += 1
            stats["total"] += 1
        except Exception as e:
            print(f"    [✗] 生成失败: {e}")

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
