"""
场景验证器
对生成的场景 JSON 进行三级验证:
  L1: JSON 格式与字段完备性检查
  L2: BDDL 语法检查
  L3: 物理合理性检查（预留）
"""

import argparse
import json
import re
from pathlib import Path
from typing import Tuple


REQUIRED_FIELDS = ["scene_id", "instruction", "category", "bddl", "objects", "robot"]

REQUIRED_BDDL_KEYWORDS = ["(:init", "(:goal"]


def validate_json_structure(scene: dict) -> Tuple[bool, list[str]]:
    """L1: 检查 JSON 结构完整性"""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in scene:
            errors.append(f"缺少必要字段: '{field}'")
    return len(errors) == 0, errors


def validate_bddl_syntax(bddl_text: str) -> Tuple[bool, list[str]]:
    """L2: 检查 BDDL 基本语法"""
    errors = []
    # 检查括号匹配
    if bddl_text.count("(") != bddl_text.count(")"):
        errors.append("BDDL 括号不匹配")

    # 检查必要关键字
    for keyword in REQUIRED_BDDL_KEYWORDS:
        if keyword not in bddl_text:
            errors.append(f"BDDL 缺少关键字: {keyword}")

    return len(errors) == 0, errors


def validate_physics(scene: dict) -> Tuple[bool, list[str]]:
    """L3: 物理合理性检查（预留接口）"""
    # TODO: 接入 Isaac Sim 或 PyBullet 进行碰撞检测等
    return True, []


def validate_scene(scene_path: str, verbose: bool = False) -> dict:
    """对单个场景执行全部验证"""
    with open(scene_path, "r", encoding="utf-8") as f:
        scene = json.load(f)

    result = {
        "scene_id": scene.get("scene_id", Path(scene_path).stem),
        "L1_pass": False,
        "L1_errors": [],
        "L2_pass": False,
        "L2_errors": [],
        "L3_pass": True,
        "L3_errors": [],
        "overall": False,
    }

    # L1
    result["L1_pass"], result["L1_errors"] = validate_json_structure(scene)

    # L2 (only if BDDL field exists)
    bddl = scene.get("bddl", "")
    if bddl:
        result["L2_pass"], result["L2_errors"] = validate_bddl_syntax(bddl)
    else:
        result["L2_errors"].append("BDDL 字段为空")

    # L3
    result["L3_pass"], result["L3_errors"] = validate_physics(scene)

    result["overall"] = result["L1_pass"] and result["L2_pass"] and result["L3_pass"]

    if verbose:
        status = "✓ 通过" if result["overall"] else "✗ 未通过"
        print(f"  [{status}] {result['scene_id']}")
        for err in result["L1_errors"] + result["L2_errors"] + result["L3_errors"]:
            print(f"    - {err}")

    return result


def main():
    parser = argparse.ArgumentParser(description="场景验证器")
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="场景 JSON 文件或目录路径")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="显示详细信息")
    args = parser.parse_args()

    input_path = Path(args.input)
    scene_files = []
    if input_path.is_dir():
        scene_files = list(input_path.glob("*.json"))
    else:
        scene_files = [input_path]

    print(f"验证 {len(scene_files)} 个场景...\n")

    results = []
    for sf in scene_files:
        r = validate_scene(str(sf), verbose=args.verbose)
        results.append(r)

    # 统计汇总
    passed = sum(1 for r in results if r["overall"])
    print(f"\n{'='*50}")
    print(f"总计: {len(results)}  通过: {passed}  未通过: {len(results) - passed}")
    print(f"通过率: {passed / len(results) * 100:.1f}%" if results else "无数据")


if __name__ == "__main__":
    main()
