from qfluentwidgets import FluentIcon

from src.tasks.MyBaseTask import MyBaseTask


class MonsterCubeTask(MyBaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动使用轮回和拾取"
        self.description = "需要只保留怪怪记忆魔方，手动选择怪怪进行，傲天需要最高等级"
        self.icon = FluentIcon.ROBOT

        from src.ocr_corrections_sub import dynamic_fix
        self.add_text_fix(dynamic_fix)

    def run(self) -> None:
        while True:
            col_p = self.calculate_color_percentage({'r': (44,45), 'g': (164,165), 'b': (186,187)}, Box(785, 392))
            if col_p > 0.8:
                self.send_key('esc')
                self.sleep(0.5)
                continue
            box1 = self.ocr(0.53, 0.35, 0.66, 0.39)
            box2 = self.ocr(0.53, 0.385, 0.66, 0.42)
            box3 = self.ocr(0.53, 0.417, 0.66, 0.452)

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

            lines = [ocr_res1, ocr_res2, ocr_res3]
            if lines.count("最终伤害:+25%") >= 3:
                self.log_info("出三终啦！！")
                self.click(812, 326)
                self.sleep(0.1)
                self.click(812, 326)
                self.sleep(0.1)
                self.click(812, 326)
                return

            # 点击空格
            self.send_key("space")
            self.sleep(0.3)
            self.send_key("space")
            self.sleep(0.3)
            self.send_key("space")
            self.sleep(1.5)