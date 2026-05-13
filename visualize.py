"""
场景可视化工具
读取 JSON 场景文件，使用 matplotlib 渲染 2D 俯视图
"""

import argparse
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path


def load_scene(scene_path: str) -> dict:
    """加载场景 JSON 文件"""
    with open(scene_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_scene_2d(scene: dict, save_path: str = None):
    """渲染 2D 俯视图"""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")

    # 绘制工作台面
    table = patches.Rectangle((-1, -1), 2, 2, linewidth=2,
                               edgecolor="black", facecolor="lightgray", alpha=0.3)
    ax.add_patch(table)

    # TODO: 从 scene 中读取物体位置并绘制
    # 示例：绘制机器人初始位置
    ax.plot(0, 0, "bo", markersize=12, label="Robot")
    ax.annotate("Robot", (0, 0.1), ha="center", fontsize=9)

    # 标注危险区域
    danger_zone = patches.Circle((0.5, 0.5), 0.3, linewidth=2,
                                  edgecolor="red", facecolor="red", alpha=0.15)
    ax.add_patch(danger_zone)
    ax.annotate("Danger Zone", (0.5, 0.85), ha="center", fontsize=8, color="red")

    ax.set_title(f"Scene: {scene.get('scene_id', 'Unknown')}\n"
                 f"Task: {scene.get('instruction', 'N/A')[:60]}")
    ax.legend(loc="lower right")

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[✓] 截图已保存: {save_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(description="场景可视化工具")
    parser.add_argument("--scene", "-s", type=str, required=True,
                        help="场景 JSON 文件路径")
    parser.add_argument("--output", "-o", type=str, default="outputs/screenshots",
                        help="截图输出目录")
    args = parser.parse_args()

    scene = load_scene(args.scene)
    scene_name = Path(args.scene).stem
    save_path = Path(args.output) / f"{scene_name}.png"
    render_scene_2d(scene, str(save_path))


if __name__ == "__main__":
    main()
