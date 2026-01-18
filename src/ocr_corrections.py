# ocr_corrections.py
import json
import re
import itertools

_RULES = [
    (r"以角色等级為[准汇]*每9级I[\w\W]*T[ ]*", "INT"),
    (r"以角色等级為[准汇]*每9级I[\w\W]*T[ ]*", "INT"),
    (r"以角色等级為[准汇]*每9级D[\w\W]*X[ ]*", "DEX"),
    (r"以角色等级為[准汇]*每9级D[\w\W]*X[ ]*", "DEX"),
    (r"以角色等级為[准汇]*每9级S[\w\W]*R[ ]*", "STR"),
    (r"以角色等级為[准汇]*每9级S[\w\W]*R[ ]*", "STR"),
    (r"以角色等级為[准汇]*每9级L[\w\W]*K[ ]*", "LUK"),
    (r"以角色等级為[准汇]*每9级L[\w\W]*K[ ]*", "LUK"),

    (r"全[国座]*性", "ALL"),
    (r"物理攻[撃擎擊 ]*力", "物理攻击力"),
    (r"魔法攻[撃擎擊 ]*力", "魔法攻击力"),
    (r"爆[馨傷撃擎擊]*傷?害?", "暴击伤害"),
    (r"技能冷[時时]間", "技能冷却时间"),

    (r"I[\w\W]*T[ ]*", "INT"),
    (r"D[\w\W]*X[ ]*", "DEX"),
    (r"S[\w\W]*R[ ]*", "STR"),
    (r"L[\w\W]*K[ ]*", "LUK"),
    (r"MAXHP", "MaxHP")
]

# 2. 基础中文错误
_RAW_ERRORS = [
    "全性", "全国性", "全座性",
    "物理攻撃力", "物理攻擎力", "物理攻擊力", "物理攻力",
    "魔法攻撃力", "魔法攻擎力", "魔法攻擊力", "魔法攻力",
    "爆害", "爆馨傷害", "爆撃害", "爆傷害", "爆馨害", "爆撃傷害", "爆擎害", "爆擎傷害",
    "技能冷時間", "技能冷时間"
]

# 3. 属性关键词
_TARGETS = ["STR", "DEX", "INT", "LUK", "MAXHP"]

# 4. 百分比后缀
_PERCENTAGES = ["13%", "12%", "11%", "10%", "9%", "8%", "7%", "6%", "5%", "3%", "1%"]


def _generate_fix_map():
    """
    内部函数：生成并返回修复字典
    """
    fix_map = {}

    # 生成属性的大小写及空格组合 (STR, Str, str ...)
    stat_errors = []
    for word in _TARGETS:
        combinations = itertools.product(*[(c.upper(), c.lower()) for c in word])
        for combo in combinations:
            base_word = "".join(combo)
            stat_errors.append(base_word)
            stat_errors.append(base_word + " ")

    level_errors = []
    prefix1 = "以角色等级為准每9级"
    prefix2 = "以角色等级為汇每9级"
    prefix3 = "以角色等级為每9级"
    for stat in stat_errors:
        if stat.lower() == 'maxhp' or stat.lower() == 'maxhp ':
            continue
        level_errors.append(f"{prefix1}{stat}+1")
        level_errors.append(f"{prefix1}{stat}+2")
        level_errors.append(f"{prefix2}{stat}+1")
        level_errors.append(f"{prefix2}{stat}+2")
        level_errors.append(f"{prefix3}{stat}+1")
        level_errors.append(f"{prefix3}{stat}+2")

    all_errors = _RAW_ERRORS + stat_errors + level_errors

    for err in all_errors:
        for pattern, target in _RULES:
            if re.search(pattern, err, re.IGNORECASE):
                if "每9级" in pattern:
                    if "1" in err:
                        fix_map[err] = target + "+1"
                    else:
                        fix_map[err] = target + "+2"
                elif "技能" in pattern:
                    for i in range(1, 3):
                        fix_map[err+f"-{i}秒"] = target + f"-{i}秒"
                else:
                    for val in _PERCENTAGES:
                        fix_map[f"{err}+{val}"] = f"{target}+{val}"
                break

    # 特殊情况手动添加
    fix_map["以角色等级為准每9级IHT+1"] = "INT+1"
    fix_map["以角色等级為准每9级IT+1"] = "INT+1"
    fix_map["以角色等级為汇每9级IT+1"] = "INT+1"
    fix_map["以角色等级為每9级IT+1"] = "INT+1"
    fix_map["以角色等级為准每9级IHT+2"] = "INT+2"
    fix_map["以角色等级為准每9级IT+2"] = "INT+2"
    fix_map["以角色等级為汇每9级IT+2"] = "INT+2"
    fix_map["以角色等级為每9级IT+2"] = "INT+2"

    return fix_map


dynamic_fix = _generate_fix_map()


if __name__ == '__main__':

    print(json.dumps(dynamic_fix, ensure_ascii=False, indent=4))
    print(f"生成的规则数量: {len(dynamic_fix)}")

    test_keys = [
        "以角色等级為准每9级IT+2",
        "Str +10%",
        "爆擎害+8%"
    ]
    print("\n--- 测试预览 ---")
    for k in test_keys:
        print(f"'{k}' -> '{dynamic_fix.get(k, '未找到')}'")