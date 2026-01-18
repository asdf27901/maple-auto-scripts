import ctypes
import os

from qfluentwidgets import FluentIcon

from src.tasks.MyBaseTask import MyBaseTask


class TestCubeTask(MyBaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.ROBOT
        self.name = "用于测试执行结果，不会洗魔方"
        self.description = "需要打开洗魔方界面，并把装备放入，选择附加潜能"
        self.default_config.update({
            "第一条测试属性": "物理攻击力+12%",
            "第二条测试属性": "物理攻击力+12%",
            "第三条测试属性": "物理攻击力+12%",
            "是否循环执行": True
        })

        from src.ocr_corrections_sub import dynamic_fix
        self.add_text_fix(dynamic_fix)

        root_path = self.executor.config["project_root"]
        # 加载dll
        dll_path = os.path.join(root_path, 'libcube64.dll')
        lib = ctypes.CDLL(dll_path)

        self.check_func = lib['?washcube@@YAPEADPEBD00@Z']
        self.check_func.restype = ctypes.c_char_p
        self.check_func.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]

    def run(self) -> None:
        while True:
            box1 = self.ocr(0.217, 0.44, 0.35, 0.48)
            box2 = self.ocr(0.217, 0.472, 0.35, 0.51)
            box3 = self.ocr(0.217, 0.5, 0.35, 0.54)

            ocr_res1 = "".join([b.name for b in box1]) if box1 else "没有识别到结果"
            ocr_res2 = "".join([b.name for b in box2]) if box2 else "没有识别到结果"
            ocr_res3 = "".join([b.name for b in box3]) if box3 else "没有识别到结果"

            res1 = ocr_res1.replace(" ", "") == self.config["第一条测试属性"]
            res2 = ocr_res2.replace(" ", "") == self.config["第二条测试属性"]
            res3 = ocr_res3.replace(" ", "") == self.config["第三条测试属性"]

            self.info_set(key="第一条属性测试结果", value=True if res1 else False)
            self.info_set(key="第二条属性测试结果", value=True if res2 else False)
            self.info_set(key="第三条属性测试结果", value=True if res3 else False)

            res_ptr: str = ctypes.cast(self.check_func(ocr_res1.encode('gbk'),
                                                       ocr_res2.encode('gbk'),
                                                       ocr_res3.encode('gbk')),
                                       ctypes.c_char_p).value.decode('gbk')
            self.info_set("dll校验结果为", res_ptr)

            if not res1 or not res2 or not res3:
                self.info_set(key="第一条识别结果", value=ocr_res1)
                self.info_set(key="第二条识别结果", value=ocr_res2)
                self.info_set(key="第三条识别结果", value=ocr_res3)
                break

            if not self.config["是否循环执行"]:
                break

            self.sleep(0.5)
