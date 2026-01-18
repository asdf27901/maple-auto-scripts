from ok import TriggerTask, Box


class MyTriggerTask(TriggerTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "用于测试执行结果，不会洗魔方"
        self.description = "需要打开洗魔方界面，并把装备方法，选择附加潜能"
        self.default_config.update({
            "第一条测试属性": "物理攻击力+12%",
            "第二条测试属性": "物理攻击力+12%",
            "第三条测试属性": "物理攻击力+12%",

            "实际测试结果1": "",
            "实际测试结果2": "",
            "实际测试结果3": ""
        })
        self.trigger_count = 0

    def run(self):
        self.trigger_count += 1
        self.log_debug(f'MyTriggerTask run {self.trigger_count}')
        box1 = self.ocr(0.217, 0.44, 0.35, 0.48)
        box2 = self.ocr(0.217, 0.472, 0.35, 0.51)
        box3 = self.ocr(0.217, 0.5, 0.35, 0.54)

        self.config["实际测试结果1"] = "".join([b.name for b in box1]) if box1 else "没有识别到结果"

        self.info_set(key="第一条属性", value="".join([b.name for b in box1]) if box1 else "没有识别到结果")
        self.info_set(key="第二条属性", value="".join([b.name for b in box2]) if box2 else "没有识别到结果")
        self.info_set(key="第三条属性", value="".join([b.name for b in box3]) if box3 else "没有识别到结果")
        self.info_set(key="当前执行次数", value=self.trigger_count)
