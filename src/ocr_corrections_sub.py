# ocr_corrections_sub.py
import json
import re
import itertools

_BASE_ATTR_RULES = [
    (r"I[\w\W]*T[\s_]*", "INT"),
    (r"D[\w\W]*X[\s_]*", "DEX"),
    (r"S[\w\W]*R[\s_]*", "STR"),
    (r"L[\w\W]*K[\s_]*", "LUK"),
    (r"MAX\s*HP[\s_]*", "MaxHP"),
]

# 中文修正规则
_CN_RULES = [
    (r"全[国座]*性", "全属性"),
    (r"[物勿][里理]攻[撃擎擊 ]*力", "物理攻击力"),
    (r"[磨麽魔][法去]攻[撃擎擊 ]*力", "魔法攻击力"),
    (r"爆[馨傷撃擎擊]*傷?害?", "暴击伤害"),
    (r"技能冷[時时]間", "技能冷却时间"),
]

# 基础属性目标
_TARGETS = ["STR", "DEX", "INT", "LUK", "MAXHP"]

# 已知的特殊 OCR 烂词
_RAW_ERRORS = [
    # 繁体识别错误项

    # 全属性
    "全性", "全国性", "全座性",

    # 物理攻击力
    "物理攻撃力", "物理攻擎力", "物理攻擊力", "物理攻力", "物里攻撃力", "物里攻擎力", "物里攻擊力", "物里攻力",
    "勿理攻撃力", "勿理攻擎力", "勿理攻擊力", "勿理攻力", "勿里攻撃力", "勿里攻擎力", "勿里攻擊力", "勿里攻力",

    # 魔法攻击力
    "魔法攻撃力", "魔法攻擎力", "魔法攻擊力", "魔法攻力", "磨法攻撃力", "磨法攻擎力", "磨法攻擊力", "磨法攻力",
    "麽法攻撃力", "麽法攻擎力", "麽法攻擊力", "麽法攻力",
    "魔去攻撃力", "魔去攻擎力", "魔去攻擊力", "魔去攻力", "磨去攻撃力", "磨去攻擎力", "磨去攻擊力", "磨去攻力",
    "麽去攻撃力", "麽去攻擎力", "麽去攻擊力", "麽去攻力",

    # 暴击伤害
    "爆害", "爆馨傷害", "爆撃害", "爆傷害", "爆馨害", "爆撃傷害", "爆擎害", "爆擎傷害",

    # 技能冷却
    "技能冷時間", "技能冷时間",

    # 属性错别字 (加入这里后，上面的正则会自动识别它们)
    "IHT", "IT", "I T", "S R", "D X", "L K"
]

# “每9级”的前缀变体
_LEVEL_PREFIXES = [
    "以角色等级為准每9级",
    "以角色等级為汇每9级",
    "以角色等级為每9级",
    "以角色等级为准每9级"
]


def _generate_candidates():
    """
    生成所有可能的 OCR 错误文本片段（大小写组合 + 列表里的烂词）
    """
    candidates = set(_RAW_ERRORS)  # 使用 set 去重

    # 自动生成 STR, Str, sTr... 以及带空格的版本
    for word in _TARGETS:
        # 生成大小写组合
        chars = [(c.upper(), c.lower()) for c in word]
        for combo in itertools.product(*chars):
            base = "".join(combo)
            candidates.add(base)
            candidates.add(base + " ")  # 尾部带空格
            candidates.add(" " + base)  # 头部带空格
            candidates.add(base + "_")

            # 生成中间带空格的版本 (如 S T R)
            if len(base) <= 3:
                candidates.add(" ".join(base))

    return list(candidates)


def _generate_fix_map():
    """
    主逻辑：候选词 -> 正则匹配 -> 生成最终字典
    """
    fix_map = {}
    candidates = _generate_candidates()

    # 合并所有规则
    all_rules = _BASE_ATTR_RULES + _CN_RULES

    for err_str in candidates:
        err_str = err_str.strip()  # 清理一下
        if not err_str:
            continue

        matched_target = None

        for pattern, target in all_rules:
            if re.search(pattern, err_str, re.IGNORECASE):
                matched_target = target
                break

        if not matched_target:
            continue

        # 技能冷却时间
        if "技能" in matched_target:
            for i in range(1, 2):
                fix_map[f"{err_str}-{i}秒"] = f"{matched_target}-{i}秒"
                fix_map[f"{err_str} -{i}秒"] = f"{matched_target}-{i}秒"
            continue

        # 普通属性
        for p in [1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
            val = f"{p}%"
            # 生成多种空格组合，确保 OCR 识别出的各种空格都能命中
            fix_map[f"{err_str}+{val}"] = f"{matched_target}+{val}"
            fix_map[f"{err_str} +{val}"] = f"{matched_target}+{val}"  # +号前有空格
            fix_map[f"{err_str} + {val}"] = f"{matched_target}+{val}"  # +号两边有空格
            fix_map[f"{err_str}+ {val}"] = f"{matched_target}+{val}"  # +号后有空格

        # 每9级属性
        if matched_target in ["STR", "DEX", "INT", "LUK"]:
            for prefix in _LEVEL_PREFIXES:
                for val in [1, 2]:
                    # 组合前缀 + 错误属性词 + 数值
                    # 比如: "以角色等级為准每9级" + "IHT" + "+1"
                    full_key = f"{prefix}{err_str}+{val}"
                    fix_map[full_key] = f"{matched_target}+{val}"

                    # 额外覆盖：前缀和属性之间有空格的情况
                    full_key_spaced = f"{prefix} {err_str}+{val}"
                    fix_map[full_key_spaced] = f"{matched_target}+{val}"

    return fix_map


dynamic_fix = _generate_fix_map()

if __name__ == '__main__':
    print(json.dumps(dynamic_fix, ensure_ascii=False, indent=4))
    print(f"生成的规则数量: {len(dynamic_fix)}")

    test_keys = [
        "以角色等级為准每9级IT+2",
        "以角色等级為汇每9级IHT+1",
        "Str +10%",  # 普通大小写
        "S R + 5%",  # 极端空格
        "爆擎害+8%",  # 中文容错
        "技能冷時間-1秒"  # 技能冷却
    ]

    print("\n--- 测试结果 ---")
    for k in test_keys:
        print(f"'{k}' -> '{dynamic_fix.get(k, '【未找到】')}'")
