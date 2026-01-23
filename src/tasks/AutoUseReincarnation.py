from ok import TriggerTask


class AutoUseReincarnation(TriggerTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动使用轮回和拾取"
        self.description = "需要手动设置轮回石碑和拾取键的快捷键"
        self.default_config.update({
            "轮回石碑快捷键": "6",
            "拾取键快捷键": "Ctrl"
        })

    def run(self):
        self.send_key(self.config['轮回石碑快捷键'])
        self.send_key(self.config['轮回石碑快捷键'])
        self.send_key(self.config['轮回石碑快捷键'])
        self.send_key(self.config['拾取键快捷键'])
        self.send_key(self.config['拾取键快捷键'])
        self.send_key(self.config['拾取键快捷键'])
