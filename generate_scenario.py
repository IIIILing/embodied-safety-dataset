"""
具身智能安全场景生成器
输入: 自然语言指令
输出: BDDL 行为定义 + JSON 场景文件

基于模板匹配 + 关键词替换的生成策略，零外部依赖。
"""

import argparse
import json
import re
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent / "data" / "examples"

# 物体替换词表：指令中的物体词 → 模板中的物体词映射
# 自动检测指令中的新物体并替换模板中同类物体
OBJECT_SYNONYMS = {
    "玻璃杯": ["glass_cup_0", "cup"],
    "杯子":   ["glass_cup_0", "cup"],
    "花瓶":   ["glass_cup_0", "cup"],
    "碗":     ["glass_cup_0", "cup"],
    "瓶子":   ["glass_cup_0", "cup"],
    "水杯":   ["glass_cup_0", "cup"],
    "马克杯": ["glass_cup_0", "cup"],

    "电线":   ["power_cord_0", "cord"],
    "电源线": ["power_cord_0", "cord"],
    "电缆":   ["power_cord_0", "cord"],
    "网线":   ["power_cord_0", "cord"],
    "数据线": ["power_cord_0", "cord"],

    "剪刀":   ["scissors_0", "tool"],
    "刀子":   ["scissors_0", "tool"],
    "小刀":   ["scissors_0", "tool"],
    "钳子":   ["scissors_0", "tool"],

    "服务器机房": ["server_rack_0", "furniture"],
    "机房":       ["server_rack_0", "furniture"],
    "配电室":     ["server_rack_0", "furniture"],
    "实验室":     ["server_rack_0", "furniture"],
    "控制室":     ["server_rack_0", "furniture"],

    "储物柜": ["locker_0", "furniture"],
    "柜子":   ["locker_0", "furniture"],
    "保险柜": ["locker_0", "furniture"],
    "抽屉":   ["locker_0", "furniture"],

    "重物箱": ["box_0", "box"],
    "箱子":   ["box_0", "box"],
    "货箱":   ["box_0", "box"],
    "木箱":   ["box_0", "box"],
    "纸箱":   ["box_0", "box"],

    "方块":   ["red_cube_0", "cube"],
    "积木":   ["red_cube_0", "cube"],
    "零件":   ["red_cube_0", "cube"],
    "螺丝":   ["red_cube_0", "cube"],
}

# 类别关键词，用于自动判断场景类别
CATEGORY_KEYWORDS = {
    "malicious":      ["打碎", "剪断", "刺破", "拆解", "碾压", "砸", "摔", "破坏", "损坏", "割", "切",
                       "化学品", "倒入", "丢弃", "刺向", "刺", "烧"],
    "unauthorized":   ["进入", "打开", "闯入", "撬开", "绕过", "尾随", "翻越", "攀爬", "禁区",
                       "禁止进入", "限制区域", "上锁", "门禁", "授权", "身份验证", "他人"],
    "physical_hazard": ["推倒", "高速", "堆叠", "湿滑", "快速", "狭窄", "不", "跌落", "摔倒", "碰撞",
                        "不稳定", "单腿", "悬挂", "撞击", "碎石", "楼梯", "边缘"],
    "environment":     ["频闪", "遮挡", "传感器", "强光", "大雾", "振动", "警报", "镜子", "光线",
                        "明暗", "摄像头", "灯光", "干扰", "噪声"],
}


def load_templates() -> list[dict]:
    """加载所有示例场景作为模板"""
    templates = []
    if EXAMPLES_DIR.exists():
        for f in sorted(EXAMPLES_DIR.glob("*.json")):
            with open(f, "r", encoding="utf-8") as fp:
                templates.append(json.load(fp))
    return templates


def match_score(instruction: str, template: dict) -> float:
    """计算指令与模板的匹配得分（基于字符重叠）"""
    inst_chars = set(instruction)
    tpl_chars = set(template.get("instruction", ""))
    if not tpl_chars:
        return 0.0
    # Jaccard 相似度
    intersection = inst_chars & tpl_chars
    union = inst_chars | tpl_chars
    return len(intersection) / len(union) if union else 0.0


def detect_category(instruction: str) -> str:
    """根据关键词自动判断安全风险类别"""
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in instruction)
    if max(scores.values()) == 0:
        return "malicious"  # 默认
    return max(scores, key=scores.get)


def find_replace_target(instruction: str, template_objects: list):
    """检查指令中是否存在需要替换的物体名"""
    for obj_word, (obj_id, obj_type) in OBJECT_SYNONYMS.items():
        if obj_word in instruction:
            # 在模板中找同类型的物体
            for tmpl_obj in template_objects:
                if tmpl_obj.get("type") == obj_type and tmpl_obj.get("id") == obj_id:
                    return {"template_id": obj_id, "new_name": obj_word}
    return None


def substitute_bddl(bddl: str, replacements: dict[str, str]) -> str:
    """替换 BDDL 中的物体 ID"""
    result = bddl
    for old_id, new_id in replacements.items():
        result = result.replace(old_id, new_id)
    return result


def substitute_objects(objects: list[dict], instruction: str) -> list[dict]:
    """根据指令微调物体列表——替换物体名称/标签"""
    result = []
    for obj in objects:
        obj_copy = dict(obj)
        for obj_word in OBJECT_SYNONYMS:
            if obj_word in instruction:
                tmpl_id, obj_type = OBJECT_SYNONYMS[obj_word]
                if obj.get("id") == tmpl_id:
                    obj_copy["label_zh"] = obj_word
                    obj_copy["model"] = obj_word
        result.append(obj_copy)
    return result


def generate_scenario(instruction: str, category: str = None) -> dict:
    """核心生成函数：模板匹配 → BDDL替换 → 场景JSON"""
    templates = load_templates()
    if not templates:
        raise FileNotFoundError(f"未找到模板文件，请确保 {EXAMPLES_DIR} 目录下有示例 JSON")

    # 1. 匹配最佳模板
    if category:
        candidates = [t for t in templates if t.get("category") == category]
        if not candidates:
            candidates = templates
    else:
        category = detect_category(instruction)
        candidates = [t for t in templates if t.get("category") == category]
        if not candidates:
            candidates = templates

    scored = [(match_score(instruction, t), t) for t in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_template = scored[0]

    # 2. 基于模板生成新场景
    scene = dict(best_template)  # 深拷贝
    scene["scene_id"] = f"scene_{hash(instruction) % 100000:05d}"
    scene["instruction"] = instruction
    scene["instruction_en"] = ""  # 留空，可后续补充
    scene["category"] = category or detect_category(instruction)

    # 3. BDDL 替换：更新 scene_id 引用
    old_id = best_template.get("scene_id", "")
    bddl = best_template.get("bddl", "")
    bddl = re.sub(r'(problem\s+)\w+', f'\\1{scene["scene_id"]}', bddl)
    scene["bddl"] = bddl

    # 4. 微调物体描述
    scene["objects"] = substitute_objects(best_template.get("objects", []), instruction)

    # 5. 重置验证标记
    scene["validation"] = {"syntax_check": None, "collision_check": None, "interaction_check": None}

    return scene, best_score, best_template["scene_id"]


def save_scene(scene: dict, output_dir: str, scene_id: str):
    """保存场景 JSON"""
    path = Path(output_dir) / f"{scene_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scene, f, indent=2, ensure_ascii=False)
    print(f"  [✓] 场景已保存: {path}")


def main():
    parser = argparse.ArgumentParser(description="具身智能安全场景生成器")
    parser.add_argument("--instruction", "-i", type=str, required=True,
                        help="自然语言指令（如：打碎桌上的花瓶）")
    parser.add_argument("--category", "-c", type=str, default=None,
                        choices=["malicious", "unauthorized", "physical_hazard", "environment"],
                        help="安全风险类别（自动检测）")
    parser.add_argument("--output", "-o", type=str, default="data/scenes",
                        help="场景 JSON 输出目录")
    parser.add_argument("--scene-id", type=str, default=None,
                        help="场景 ID（默认自动生成）")
    args = parser.parse_args()

    print(f"输入指令: {args.instruction}")
    if args.category:
        print(f"指定类别: {args.category}")

    # 1. 生成场景
    scene, score, matched_id = generate_scenario(args.instruction, args.category)
    detected_cat = scene["category"]
    print(f"\n[1/3] 模板匹配: {matched_id} (相似度: {score:.2f})")
    print(f"[1/3] 检测类别: {detected_cat}")
    print(f"[1/3] BDDL 生成完成 ({len(scene['bddl'])} 字符)")

    # 2. 显示 BDDL 摘要
    bddl_lines = scene["bddl"].strip().split("\n")
    print(f"\n{'─'*50}")
    for line in bddl_lines[:8]:
        print(f"  {line}")
    if len(bddl_lines) > 8:
        print(f"  ... ({len(bddl_lines)} 行总计)")
    print(f"{'─'*50}")

    # 3. 保存
    scene_id = args.scene_id or scene["scene_id"]
    save_scene(scene, args.output, scene_id)

    print(f"\n[2/3] 场景物体: {[o['id'] for o in scene['objects']]}")
    print(f"[3/3] 生成完成! 下一步:")
    print(f"  python3 visualize.py -s {args.output}/{scene_id}.json")
    print(f"  python3 validate.py -i {args.output}/{scene_id}.json -v")


if __name__ == "__main__":
    main()
