# 数据集使用指南

## 数据加载

```python
import json

# 加载单个场景
with open("data/scenes/scene_0000.json", "r", encoding="utf-8") as f:
    scene = json.load(f)

print(f"指令: {scene['instruction']}")
print(f"类别: {scene['category']}")
print(f"BDDL: {scene['bddl'][:100]}...")
print(f"物体数: {len(scene['objects'])}")
```

## BDDL 解析

BDDL (Behavior Domain Definition Language) 使用 Lisp-like 语法，核心结构：

- `(define (problem <name>) ...)` — 场景定义
- `(:objects ...)` — 实体声明 (robot, table, tool, zone)
- `(:init ...)` — 初始状态 (位置, 姿态, 属性)
- `(:goal ...)` — 目标状态 (安全风险的结果)

## 场景分类标准

| 类别 | 判定关键词 | 风险描述 |
|------|-----------|---------|
| malicious | 打碎, 剪断, 拆解, 碾压, 化学品 | 蓄意破坏财产 |
| unauthorized | 进入, 闯入, 撬开, 绕过, 禁区 | 越权访问受限区域 |
| physical_hazard | 推倒, 高速, 湿滑, 堆叠, 不稳定 | 物理安全事故 |
| environment | 频闪, 遮挡, 大雾, 振动, 警报 | 环境感知干扰 |

## API 接口说明

```bash
# generate_scenario.py 生成场景
python3 generate_scenario.py \
  --instruction "输入指令" \
  --category "malicious" \      # 可选，自动检测
  --use-api                     # 使用 DeepSeek API
```

输出：`data/scenes/<scene_id>.json`
