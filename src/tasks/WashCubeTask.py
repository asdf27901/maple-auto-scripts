import ctypes
import os
from typing import Optional, Any, Generator, Tuple

from ok.__init__ import Box
from qfluentwidgets import FluentIcon

from src.tasks.MyBaseTask import MyBaseTask


class WashCubeTask(MyBaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "点我洗附加潜能"
        self.description = "展开配置项进行配置"
        self.icon = FluentIcon.CLOUD
        self.default_config.update({
            '魔方类型': [],
            '期望属性': [],
            '结果类型': [],
            '需要洗的装备件数': 1,
            '速率因子': 1.0,
        })
        self.config_type["魔方类型"] = {'type': "multi_selection",
                                        'options': ['Precious cube', 'Absolute cube']}
        self.config_type['期望属性'] = {'type': 'multi_selection',
                                        'options': [
                                            '物攻', '魔攻',
                                            '力量', '敏捷', '智力', '运气', '血量', '全属性',
                                            '1爆伤(需要勾选上方属性)', '2爆伤(需要勾选上方属性)', '3爆伤(需要勾选上方属性)',
                                            '1冷却(需要勾选上方属性)', '2冷却(需要勾选上方属性)', '3冷却(需要勾选上方属性)',
                                            '测试(勾选了之后洗一下就换装备)'
                                        ]}
        self.config_type['结果类型'] = {'type': 'multi_selection',
                                        'options': ["大大大", "大大小"]}
        self.config_description.update({
            "魔方类型": "魔方会在已选中进行选择，\n优先珍贵附加魔方，如果都没有了则脚本结束",
            "需要洗的装备件数": "会根据输入数量生成n*4的矩阵\n例如输入：11，生成如下：\n□ □ □ □\n□ ■ □ □\n□ □ ■\n只会找其中有颜色的格子洗",
            "速率因子": "用于控制洗魔方速度，越小速率越快，建议值：1"
        })

        from src.ocr_corrections_sub import dynamic_fix
        self.add_text_fix(dynamic_fix)

        root_path = self.executor.config["project_root"]
        # 加载dll
        dll_path = os.path.join(root_path, 'src', 'libcube64.dll')
        lib = ctypes.CDLL(dll_path)

        self.check_func = lib['?washcube@@YAPEADPEBD00@Z']
        self.check_func.restype = ctypes.c_char_p
        self.check_func.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self.rate = 1

    def run(self) -> None:
        self.log_info(f"任务执行配置为：{self.config}")

        self.rate = self.config['速率因子']
        self.log_info(f"配置速率因子为: {self.config['速率因子']}")
        # 校验任务配置
        if not self.config['魔方类型'] \
                or not self.config['期望属性'] \
                or not self.config['结果类型']:
            self.notification("没有勾选任务配置，执行失败")
            return

        if self.config['需要洗的装备件数'] <= 0 or self.config['需要洗的装备件数'] > 28:
            self.notification("输入装备件数有误，任务无法执行")
            return

        # 判断是否打开了背包
        if self.open_bag() is False:
            return

        boxx = self.find_feature('button', horizontal_variance=1, vertical_variance=1, threshold=0.95)
        if not boxx:
            self.log_error('没有找到装备强化按钮，请重试')
            return
        self.log_info(f"装备强化按钮坐标为：{boxx[0].center()}")
        # 点击按钮中心坐标
        # 这里点3次是为了防止抓到了装备导致点击失败
        self.click(*boxx[0].center())
        self.click(*boxx[0].center())
        self.click(*boxx[0].center())
        self.sleep(1 * self.rate)

        apd_box = self.find_feature("Additional potential deactivate", vertical_variance=0.1, horizontal_variance=0.1)
        if not apd_box:
            self.log_error('没有【附加潜在能力】按钮，退出程序')
            return
        self.sleep(0.5)
        self.click(*apd_box[0].center())
        self.click(*apd_box[0].center())

        self.sleep(1 * self.rate)
        equ_boxes = (Box(
            x=625 + (i % 4) * 47,
            y=173 + (i >> 2) * 47,
            width=43,
            height=43
        ) for i in range(self.config['需要洗的装备件数'] or 1))

        try:
            self.wash_equipments(equ_boxes, apd_box[0])
        except StopIteration:
            self.log_info("没有装备可以洗了")

    def open_bag(self) -> bool:
        """
        打开背包
        Returns:
        """
        self.click(0.5, 0.5)
        self.sleep(1 * self.rate)

        times = 0
        # 检查是否出现背包特征，如果没有出现，则再按下一次"i"
        box = self.check_bag_is_opened()
        while not box:
            times += 1
            self.send_key('i')
            self.sleep(1 * self.rate)
            if box := self.check_bag_is_opened():
                break
            if times >= 3:
                self.log_error('最终无法打开背包，退出程序')
                return False

        self.mouse_down(*box.center())
        self.sleep(0.5)
        self.move(345, 126)
        self.sleep(0.5)
        self.mouse_up()
        self.log_info('背包打开成功')
        return True

    def check_bag_is_opened(self) -> Optional[Box]:
        """
        检查背包特征，判断是否已打开
        Returns:
        """

        box = self.find_feature('title', horizontal_variance=1, vertical_variance=1, threshold=0.95)

        if not box:
            self.log_error('完全没有识别到背包特征，给钱帮忙检查, 1分钟50U')
            return None
        return box[0]

    def wash_equipments(self, boxes: Generator, apd_box: Box):
        """
        洗装备逻辑
        Args:
            boxes:
            apd_box:
        Returns:
        """
        # 获取期望使用的魔方
        cubes = self.config["魔方类型"]
        equ_box = next(boxes)

        # 先找魔方，如果魔方都没，直接拜拜
        for cube in cubes:
            cue_box = self.find_one(feature_name=cube, vertical_variance=0.1, horizontal_variance=0.13)
            if cue_box is None:
                self.log_error(f"没有找到{cube}")
                continue

            # 根据灰度占比判断是否有装备放置
            while self.check_rgc_percentage(r=(200, 229), g=(200, 229), b=(200, 229), equ_box=equ_box):
                # 进入此方法说明灰度占比超过80%，说明此时equ_box没有装备占用，调用生成器对象
                equ_box = next(boxes)

            # 说明已经找到了装备，那么就先选中魔方和装备
            self.select_cube_and_equ(cue_box, equ_box)

            while True:
                success_icon = self.key_down_space_and_find_success_icon()
                if not success_icon:
                    self.log_error("没有识别到Success特征，切换tab尝试")
                    self.sleep(2)
                    self.click(84, 430)
                    self.sleep(0.4)
                    self.click(84, 430)
                    self.sleep(0.4)
                    self.click(*apd_box.center())
                    self.sleep(0.4)
                    self.click(*apd_box.center())
                    self.sleep(0.4)
                    self.click(*cue_box.center())
                    self.sleep(0.5)
                    self.move(390, 715)
                    continue
                self.sleep(1.5 * self.rate)

                res, cue_box = self.check_cube_result(cube=cube)

                if cue_box is None:
                    self.log_info(f"{cube} 用完了，尝试下一种魔方")
                    break

                if res:
                    self.log_info("当前装备洗成功，切换下一个")
                    equ_box = next(boxes)

                    # 检查新装备是否为空位
                    while self.check_rgc_percentage(r=(200, 229), g=(200, 229), b=(200, 229), equ_box=equ_box):
                        equ_box = next(boxes)

                    self.select_cube_and_equ(cue_box, equ_box)
                    self.sleep(0.5)

    def select_cube_and_equ(self, cue_box: Box, equ_box: Box):
        # 选中魔方
        self.click(cue_box)
        self.click(cue_box)

        self.sleep(0.5)

        # 右键选中装备
        self.right_click(equ_box)
        self.sleep(0.1)
        self.right_click(equ_box)
        self.sleep(0.1)
        self.right_click(equ_box)
        self.sleep(0.1)

    def key_down_space_and_find_success_icon(self) -> Optional[Box]:
        # 按下空格开始洗
        self.send_key('space')
        self.sleep(0.4 * self.rate)
        self.send_key('space')
        self.sleep(0.4 * self.rate)
        self.send_key('space')

        self.log_info('已完成洗魔方空格按下')

        return self.wait_feature(
            feature="Success",
            horizontal_variance=0.1,
            vertical_variance=0.1,
            threshold=0.7,
            time_out=5
        )

    def check_cube_result(self, cube: str) -> Tuple[bool, Optional[Box]]:

        # 检查逻辑...
        box1 = self.ocr(0.217, 0.44, 0.35, 0.48)
        box2 = self.ocr(0.217, 0.472, 0.35, 0.51)
        box3 = self.ocr(0.217, 0.5, 0.35, 0.54)

        ocr_res1 = "".join([b.name for b in box1]) if box1 else "没有识别到结果"
        ocr_res2 = "".join([b.name for b in box2]) if box2 else "没有识别到结果"
        ocr_res3 = "".join([b.name for b in box3]) if box3 else "没有识别到结果"

        self.info_set(key="第一条属性", value=ocr_res1)
        self.info_set(key="第二条属性", value=ocr_res2)
        self.info_set(key="第三条属性", value=ocr_res3)

        self.log_info('洗出的三条属性为：\n'
                      f'第一条：{ocr_res1}\n'
                      f'第二条：{ocr_res2}\n'
                      f'第三条：{ocr_res3}')

        if '测试' in "".join(self.config['期望属性']):
            cube_box = self.find_one(
                feature_name=cube,
                vertical_variance=0.1,
                horizontal_variance=0.13,
                threshold=0.8  # 选中会出现蓝色背景，降低置信度
            )
            return True, cube_box

        # 将获取结果组装成列表传入
        lines = [ocr_res1.encode('gbk'), ocr_res2.encode('gbk'), ocr_res3.encode('gbk')]
        res = self.get_result_from_washcube_dll(lines, expect_attr=self.config['期望属性'], expect_type=self.config['结果类型'])

        # 检查完了查看之前执行的魔方还有没有
        # 如果没有了，则进入下一个魔方队列
        cube_box = self.find_one(
            feature_name=cube,
            vertical_variance=0.1,
            horizontal_variance=0.13,
            threshold=0.8  # 选中会出现蓝色背景，降低置信度
        )

        return res, cube_box

    def check_rgc_percentage(
            self,
            r: Tuple[int, int], g: Tuple[int, int], b: Tuple[int, int],
            equ_box: Box
    ) -> bool:
        """
        计算所选Box中灰度占比
        """
        rgb_p = self.calculate_color_percentage({'r': r, 'g': g, 'b': b}, equ_box)
        return rgb_p > 0.8

    def get_result_from_washcube_dll(self, lines: list[bytes], expect_attr: list[str], expect_type: list[str]) -> bool:
        res_ptr: str = ctypes.cast(self.check_func(*lines), ctypes.c_char_p).value.decode('utf-8')

        self.info_set("dll返回结果为", res_ptr)

        if '垃圾' in res_ptr:
            return False

        res_l = res_ptr.split('|')
        res_type = res_l[0]
        res_attr = res_l[1]
        attr_num = res_l[2]
        extra_attr = res_l[3]

        if res_type not in expect_type:
            return False

        if res_attr not in "".join(expect_attr):
            return False

        # 如果是暴伤或者冷却，那么判断是否符合词条数目
        if res_attr in ['爆伤', '冷却'] \
                and (attr_num + res_attr) not in "".join(expect_attr) \
                or (extra_attr != '未知' and extra_attr not in expect_attr):
            return False
        elif int(attr_num) <= 1:
            return False

        return True

    def validate_config(self, key: str, value: Any) -> Optional[str]:
        """
        用于校验当前任务配置是否正确
        Args:
            key:
            value:
        Returns:
        """
        if key == "魔方类型" and not value:
            self.log_error("没有勾选魔方类型，任务无法执行")
            return "没有勾选魔方类型，任务无法执行"
        if key == "期望属性" and not value:
            self.log_error("没有勾选期望属性，任务无法执行")
            return "没有勾选期望属性，任务无法执行"
        if key == "结果类型" and not value:
            self.log_error("没有勾选结果类型，任务无法执行")
            return "没有勾选结果类型，任务无法执行"
        if key == "需要洗的装备件数" and (not value or value <= 0 or value > 28):
            self.log_error("输入装备件数有误，任务无法执行")
            return "输入装备件数有误，任务无法执行"
