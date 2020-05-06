class QssTool:
    @staticmethod
    def set_qss(obj, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
        	style = f.read()
        print(style)
        obj.setStyleSheet(style)
