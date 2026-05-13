"""
具身智能安全场景生成器
输入: 自然语言指令
输出: BDDL 行为定义 + JSON 场景文件
"""

import argparse
import json
import os
from pathlib import Path

# TODO: 接入 LLM API
# from openai import OpenAI


def generate_bddl(instruction: str, objects: list[str] = None) -> str:
    """将自然语言指令转为 BDDL 行为定义"""
    # TODO: 调用 LLM API 生成
    pass


def bddl_to_scene_json(bddl_text: str, instruction: str, category: str = "unsafe") -> dict:
    """将 BDDL 文本转为 JSON 场景配置"""
    # TODO: 解析 BDDL，构建场景 JSON
    pass


def save_scene(scene: dict, output_dir: str, scene_id: str):
    """保存场景 JSON 到指定目录"""
    path = Path(output_dir) / f"{scene_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scene, f, indent=2, ensure_ascii=False)
    print(f"[✓] 场景已保存: {path}")


def main():
    parser = argparse.ArgumentParser(description="具身智能安全场景生成器")
    parser.add_argument("--instruction", "-i", type=str, required=True,
                        help="自然语言指令")
    parser.add_argument("--category", "-c", type=str, default="unsafe",
                        choices=["malicious", "unauthorized", "physical_hazard", "environment"],
                        help="安全风险类别")
    parser.add_argument("--output", "-o", type=str, default="data/scenes",
                        help="场景 JSON 输出目录")
    parser.add_argument("--scene-id", type=str, default=None,
                        help="场景 ID（默认自动生成）")
    args = parser.parse_args()

    # 1. 生成 BDDL
    bddl = generate_bddl(args.instruction)
    print(f"[1/3] BDDL 生成完成\n{bddl[:200]}...")

    # 2. 转为场景 JSON
    scene = bddl_to_scene_json(bddl, args.instruction, args.category)

    # 3. 保存
    scene_id = args.scene_id or f"scene_{hash(args.instruction) % 100000:05d}"
    save_scene(scene, args.output, scene_id)


if __name__ == "__main__":
    main()
