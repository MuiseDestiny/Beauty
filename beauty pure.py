from PyQt5.QtWidgets import QWidget
from PIL import Image
from PyQt5.Qt import *
import requests
import sip
from datetime import datetime
from QssTool import QssTool
from io import BytesIO
from PyQt5.QtCore import Qt
from threading import Thread
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QGraphicsOpacityEffect
import sys
import random
import re
import os


class MyFrame(QFrame):
    enter_signal = pyqtSignal()
    leave_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._radius = 0
        self.shadow_op = QGraphicsDropShadowEffect(self)

    def enterEvent(self, *args):
        self.enter_signal.emit()
        return super().enterEvent(*args)

    def leaveEvent(self, *args):
        self.leave_signal.emit()
        return super().leaveEvent(*args)

    @pyqtProperty(float)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        self.shadow_op.setColor(Qt.gray)
        self.shadow_op.setOffset(0, r / 20 * 5)
        self.shadow_op.setBlurRadius(r)
        self.setGraphicsEffect(self.shadow_op)
        self._radius = r


class MyPushButton(QPushButton):

    def __init__(self, parent):
        super().__init__(parent)
        self._opacity = 0
        self.opacity_op = QGraphicsOpacityEffect(self)

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, o):
        # self.opacity_op = QGraphicsOpacityEffect(self)
        self.opacity_op.setOpacity(o)
        self.setGraphicsEffect(self.opacity_op)
        self._opacity = o
        if o > 0:
            self.opacity_op.setOpacity(o)
            self.setGraphicsEffect(self.opacity_op)
            self._opacity = o
            self.setHidden(False)
        elif o == 0:
            self.setHidden(True)


class UpdatePic(QThread):
    api_list = ['https://acg.xydwz.cn/gqapi/gqapi.php', 'https://m.yu.cx/tool/tu', 'http://api.mtyqx.cn/api/random.php',
                'https://acg.xydwz.cn/api/api.php', 'http://api.btstu.cn/sjbz/?lx=dongman',
                'http://api.mtyqx.cn/tapi/random.php', 'https://api.ixiaowai.cn/gqapi/gqapi.php',
                'http://illii.cn/api.php', 'http://api.btstu.cn/sjbz/?lx=suiji', 'https://api.ixiaowai.cn/api/api.php',
                'https://img.xjh.me/random_img.php', 'https://bing.ioliu.cn/v1/rand',
                'https://img.xjh.me/random_img.php?type=bg&ctype=nature&return=302',
                'http://api.btstu.cn/sjbz/?lx=meizi', 'https://unsplash.it/1600/900?random',
                'https://api.dujin.org/pic/', 'http://api.btstu.cn/sjbz/zsy.php',
                ' https://api.ixiaowai.cn/gqapi/gqapi.php', 'http://www.dmoe.cc/random.php']
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    }
    download_finish = pyqtSignal()
    return_n = 0

    def __init__(self, filename):
        super().__init__()
        self.filepath = 'pngs/' + filename + '.jpg'
        self.pic_w = 300
        self.pic_h = 450
        self.scale = self.pic_w / self.pic_h

    def run(self):
        self.return_n += 1
        if self.return_n == 6:
            return
        api = random.choice(self.api_list)
        try:
            res = requests.get(api, headers=self.headers, timeout=5)
            img = self.clip_img(Image.open(BytesIO(res.content)))
            img = img.resize((self.pic_w, self.pic_h))
            img.save(self.filepath)
            self.download_finish.emit()
        except Exception as e:
            print(e)
            return self.run()

    def clip_img(self, img):
        ww, hh = img.size
        ori_scale = ww / hh
        if ori_scale >= self.scale:
            return img.crop((0, 0, hh * self.scale, hh))
        elif ori_scale < self.scale:
            return img.crop((0, 0, ww, ww / self.scale))


class SeriesAnimation(QParallelAnimationGroup):
    """
    实现三个动画:
    1. 整体上下浮动
    2. 阴影效果
    3. 按钮慢慢浮现
    """
    dur = 233

    def __init__(self, *args):
        super().__init__()
        self.obj, self.is_up, self.max_radius, self.max_offset_y, self._self, self.i = args
        # 初始化浮动动画
        self.init_up_down_anim(self.obj)
        # 阴影渐变效果
        self.init_shadow_anim(self.obj)
        # 左右按键渐变
        self.init_opacity_anim_right(self.obj.findChild(MyPushButton, 'Right'))
        self.init_opacity_anim_left(self.obj.findChild(MyPushButton, 'Left'))
        # 创建动画组
        self.addAnimation(self.up_down_anim)

        self.addAnimation(self.right_opacity_anim)
        self.addAnimation(self.left_opacity_anim)
        self.addAnimation(self.shadow_anim)

    def init_up_down_anim(self, obj):
        self.up_down_anim = QPropertyAnimation()
        self.up_down_anim.setTargetObject(obj)
        self.up_down_anim.setPropertyName(b'pos')
        self.up_down_anim.setDuration(self.dur)
        self.up_down_anim.setStartValue(obj.pos())
        self.up_down_anim.setEndValue(QPoint(obj.pos().x(), 0 if self.is_up else 25))
        self.up_down_anim.setEasingCurve(QEasingCurve.InCurve)

    def init_shadow_anim(self, obj):
        self.shadow_anim = QPropertyAnimation()
        self.shadow_anim.setTargetObject(obj)
        self.shadow_anim.setDuration(self.dur)
        self.shadow_anim.setPropertyName(b'radius')
        self.shadow_anim.setStartValue(obj._radius)
        self.shadow_anim.setEndValue(self.max_radius if self.is_up else 0)
        self.shadow_anim.setEasingCurve(QEasingCurve.InCurve)

    def init_opacity_anim_left(self, obj):
        self.left_opacity_anim = QPropertyAnimation()
        self.left_opacity_anim.setTargetObject(obj)
        self.left_opacity_anim.setDuration(self.dur)  # 一次循环时间
        self.left_opacity_anim.setPropertyName(b'opacity')
        self.left_opacity_anim.setStartValue(obj._opacity)
        self.left_opacity_anim.setEndValue(0.999 if self.is_up else 0)
        self.left_opacity_anim.setEasingCurve(QEasingCurve.InCurve)

    def init_opacity_anim_right(self, obj):
        self.right_opacity_anim = QPropertyAnimation()
        self.right_opacity_anim.setTargetObject(obj)
        self.right_opacity_anim.setDuration(self.dur)  # 一次循环时间
        self.right_opacity_anim.setPropertyName(b'opacity')
        self.right_opacity_anim.setStartValue(obj._opacity)
        self.right_opacity_anim.setEndValue(0.999 if self.is_up else 0)
        self.right_opacity_anim.setEasingCurve(QEasingCurve.InCurve)


class Beauty(QWidget):
    weather_list = []
    frame_list = []
    frame_history_list = []
    next_index = 0
    current_suggest_api = ''
    current_weather_api = ''
    is_finish = True
    update_pic = None
    anim_thread_dict = {}
    anim_thread = None
    params = dict.fromkeys([str(i) for i in range(7)])
    number_key = None
    timer = None
    suggest_api = 'http://toy1.weather.com.cn/search?cityname='
    weather_api = 'http://www.weather.com.cn/weather/{}.shtml'

    def __init__(self):
        super().__init__()
        self.resize(1200, 745)
        self.setFixedWidth(1200)
        self.setFixedHeight(745)
        self.setObjectName('win')
        self.scroll = QScrollArea()
        self.h_box = QGridLayout()
        self.h_box_bg = QLabel()
        self.v_box = QVBoxLayout()
        self.title = QLabel()
        self.title.installEventFilter(self)
        self.input_edit = QLineEdit()
        self.sb = QScrollBar()
        self.completer = QCompleter()
        self.popup = self.completer.popup()
        self.model = QStringListModel()
        self.popup.setObjectName('completerPopup')
        self.popup.setStyleSheet("""QListView {
            background-color: white;
            border: 2px solid grey;
            selection-color: white;
            selection-background-color: gray;
            text-align: center;}""")
        self.popup.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.input_btn = QAction(self.input_edit)
        self.setWindowTitle('Weather')
        self.setWindowIcon(QIcon('pngs/晴.png'))
        self.init_ui()
        self.root = os.environ.get('TEMP') + '\\beauty.txt'
        # 读取历史数据 格式为列表 [搜索的城市， 选择的代号]
        self.read()
        # 更新天气数据
        self.update_data()
        # 水平滑条
        self.scroll.setWidget(self.h_box_bg)
        self.v_box.addWidget(self.scroll)
        # 设定布局
        self.setLayout(self.v_box)

    def init_ui(self):
        """
        初始化窗体界面，搜索框，下面的区域
        """
        for key in self.params.keys():
            self.params[key] = {
                'class': None,
                'style': None
            }
        self.title.setText("<font color=#fa744f style='font-size: 40px;font-weight: bold;'>W</font>"
                           "<font color=#16817a style='font-size: 40px;font-weight: bold;'>e</font>"
                           "<font color=#77d8d8 style='font-size: 40px;font-weight: bold;'>a</font>"
                           "<font color=#ff7272 style='font-size: 40px;font-weight: bold;'>t</font>"
                           "<font color=#ffb6b6 style='font-size: 40px;font-weight: bold;'>h</font>"
                           "<font color=#aacfcf style='font-size: 40px;font-weight: bold;'>e</font>"
                           "<font color=#ffb385 style='font-size: 40px;font-weight: bold;'>r</font>")
        self.h_box_bg.setObjectName('h_box_frame')
        self.h_box_bg.setFixedHeight(500)
        self.h_box_bg.setFixedWidth(450 * 6)
        self.input_edit.setFont(QFont("微软雅黑", 12, QFont.Bold))
        self.input_edit.setPlaceholderText('Your location')
        self.input_edit.setFixedWidth(450)
        self.input_edit.setAlignment(Qt.AlignCenter)
        self.input_edit.textChanged.connect(self.set_location)
        self.input_edit.setCompleter(self.completer)
        self.completer.setCompletionMode(QCompleter.InlineCompletion)
        self.input_btn.setIcon(QIcon('pngs/scope.png'))
        self.input_edit.addAction(self.input_btn, self.input_edit.TrailingPosition)
        self.input_btn.setShortcut('Enter')
        self.input_btn.triggered.connect(self.update_data)
        # 添加到垂直布局
        self.v_box.addWidget(self.title, alignment=Qt.AlignCenter)
        self.v_box.addWidget(self.input_edit, alignment=Qt.AlignCenter)
        self.v_box.setSpacing(20)
        self.v_box.setContentsMargins(45, 50, 45, 50)
        self.setLayout(self.v_box)
        # 步长
        self.scroll.setHorizontalScrollBar(self.sb)
        self.sb.setSingleStep(400)
        self.sb.setPageStep(400)
        # 应用布局 美化
        QssTool.set_qss(self, 'beauty.qss')
        # 初始化彩条
        from matplotlib.colors import LinearSegmentedColormap
        import matplotlib as mpl
        self.lsc_cmap = LinearSegmentedColormap.from_list('mycolor', colors=['#5ACEBE', '#FFACB7', '#FF576F', '#D22D00'])
        self.norm = mpl.colors.Normalize(vmin=-20, vmax=40)

    def tem_to_color(self, tem):
        color = '({},{},{})'.format(*[int(i*255) for i in list(self.lsc_cmap(self.norm(int(tem))))[:3]])
        return color

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def change_pic(self, obj):
        """
        图片控制，首先获取一张图片替换原图，然后重新设置qss
        """
        self.leave_anim(obj)
        try:
            filename = obj.property('number')
            self.update_pic = UpdatePic(filename)
            self.update_pic.download_finish.connect(lambda: obj.setStyleSheet(""".MyFrame[number='{}']:hover
            {{background: url('pngs/{}.jpg');}}
            {}""".format(filename, filename, self.params[filename]['style'])))
            self.update_pic.start()
        except Exception as e:
            print('When Beauty changed the picture, ' + str(e))

    def init_weather(self, parent, mask):
        """
        parent就是底层frame, 在上面添加小部件
        """
        data = self.weather_list[self.next_index]
        v_box = QVBoxLayout()
        day_weather = data['weather'].split('转') if '转' in data['weather'] else [''] + [data['weather']]
        wea_morning = QLabel(
            "<img src='pngs/{}.png'></img>".format(day_weather[0] if len(day_weather[0]) else '透明'))  # 上午天气
        top_box = QHBoxLayout()
        btn_left = MyPushButton(mask)
        btn_left.setObjectName('Left')
        btn_right = MyPushButton(mask)
        btn_right.setObjectName('Right')
        # 设置隐藏
        btn_list = [btn_right, btn_left]
        for i, btn in enumerate(btn_list):
            btn.hide()
            btn.setFlat(True)
        # 绑定
        btn_right.clicked.connect(lambda: self.add_click(parent))
        btn_left.clicked.connect(lambda: self.change_pic(parent))
        # 布局
        top_box.addWidget(btn_left, alignment=Qt.AlignLeft)
        top_box.addWidget(wea_morning, alignment=Qt.AlignCenter)
        top_box.addWidget(btn_right, alignment=Qt.AlignRight)
        # 左 上 右 下
        top_box.setContentsMargins(25, 20, 25, 0)
        # 下午天气
        wea_afternoon = QLabel("<img src='pngs/{}.png'></img>".format(day_weather[1]))  # 下午天气
        wea_info = QLabel(
            "<font color='white' style='font-size: 20px;font-weight: bold;'>{}</font>".format(data['weather']))  # 天气描述
        wea_temperature = QLabel(
            "<font color='white' style='font-size: 25px;font-weight: bold;'>{}</font>".format(data['temperate']))  # 温度
        # 水平盒子
        h_box = QHBoxLayout()
        if len(data['wind']) == 2:
            start_direction = QLabel("<img src='pngs/{}.png'></img>".format(data['wind'][0]))  # 开始风向
            end_direction = QLabel("<img src='pngs/{}.png'></img>".format(data['wind'][1]))  # 结束风向
            h_box.addWidget(start_direction, alignment=Qt.AlignCenter)
            h_box.addWidget(end_direction, alignment=Qt.AlignCenter)
            h_box.setContentsMargins(80, 0, 80, 0)
            wind_info = QLabel(
                "<font color='white' style='font-size: 20px;'>{}</font>".format('转'.join(data['wind'])))  # 风描述
        else:
            now_direction = QLabel("<img src='pngs/{}.png'></img>".format(data['wind'][0]))
            h_box.addWidget(now_direction, alignment=Qt.AlignCenter)
            wind_info = QLabel("<font color='white' style='font-size: 20px;'>{}</font>".format(data['wind'][0]))  # 风描述
        # 下面的时间
        day_text = data['day'].replace('）', '').split('日（')[1]
        day_number = data['day'].split('日')[0]
        wea_time = QLabel("<font color='#d8345f' style='font-size: 40px;font-weight: bold;'>{}</font>"
                          "<br></br>"
                          "<font color='gray' style='font-size: 20px;font-weight: bold;'>{}</font>".format(day_number, day_text))  # 时间
        wea_time.setObjectName('bottom')
        wea_time.setAlignment(Qt.AlignCenter)
        wea_time.setFixedWidth(300)
        wea_time.setFixedHeight(100)
        # 水平盒子
        v_box.addLayout(top_box)
        v_box.addWidget(wea_afternoon, alignment=Qt.AlignCenter)
        v_box.addWidget(wea_info, alignment=Qt.AlignCenter)
        v_box.addWidget(wea_temperature, alignment=Qt.AlignCenter)
        v_box.addLayout(h_box)
        v_box.addWidget(wind_info, alignment=Qt.AlignCenter)
        v_box.addWidget(wea_time, alignment=Qt.AlignCenter)
        v_box.setContentsMargins(0, 0, 0, 0)
        temperature_list = data['temperate'].replace('℃', '').split(' to ')
        low_tem, high_tem = temperature_list if len(temperature_list) == 2 else temperature_list * 2
        return v_box, low_tem, high_tem

    def product_frame(self):
        """
        用来生产一个frame，并将frame默认背景色根据温度产生渐变
        """
        frame = MyFrame()
        frame.setProperty('number', str(self.next_index))
        frame.enter_signal.connect(lambda: self.enter_anim(frame))
        frame.leave_signal.connect(lambda: self.leave_anim(frame))
        frame.setObjectName('frame_box')
        frame.setFixedHeight(450)
        frame.setFixedWidth(300)
        frame_mask = QFrame(frame)
        frame_mask.setObjectName('mask')
        frame_mask.setFixedHeight(450)
        frame_mask.setFixedWidth(300)
        box, low_tem, high_tem = self.init_weather(frame, frame_mask)
        frame_mask.setLayout(box)
        fore_style = """.MyFrame#frame_box:hover {{background: url('pngs/{}.jpg');}}
                        .MyFrame#frame_box {{background-color: qlineargradient(spread:pad,
                        x1:0,y1:0,x2:0,y2:1,
                        stop:0 rgb{},
                        stop:0.6 rgb{},
                        stop:1 rgb{});}}""".format(self.next_index + 1,
                        self.tem_to_color(low_tem), self.tem_to_color(high_tem),
                        self.tem_to_color(high_tem))
        self.params[str(self.next_index)]['style'] = fore_style
        frame.setStyleSheet(fore_style)
        return frame

    def init_frame_box(self):
        """
        首先隐藏上次的frame，然后在栅格布局中添加新的
        """
        for box in self.frame_list:
            box.hide()
        for i in range(7):
            self.next_index = i
            frame = self.product_frame()
            self.h_box.addWidget(frame, 0, i)
            self.frame_list.append(frame)
        self.h_box.setSpacing(100)
        self.h_box_bg.setLayout(self.h_box)

    def get_weather(self):
        """
        天气获取，用正则，也可用xpath，没必要
        """
        print(self.current_weather_api)
        r = requests.get(self.current_weather_api, headers={
        # 'Host': 'www.weather.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'})
        r.encoding= 'utf-8'
        orignal_list = re.findall(r'<h1>(\d{1,2}日.+)</h1>\n<big class="png.+"></big>\n<big class="png.+"></big>\n<p title=".+" class=".+">(.+)</p>\n<p class="tem">\n([\s\S+]+?)\n</p>\n<p class="win">\n<em>\n([\s\S]+?)</em>\n<i>(.+)</i>', r.text)
        wea_list = []
        for wea in orignal_list:
            wea_dict = {}
            wea_dict['day'] = wea[0]
            wea_dict['weather'] = wea[1]
            wea_dict['temperate'] = '℃ to '.join(re.findall('(\d{1,2}℃*)', wea[2]))
            wea_dict['wind'] = re.findall('title="(.{,6})"', wea[3])
            wea_dict['wind_info'] = wea[4]
            wea_list.append(wea_dict)
        print(wea_list)
        self.weather_list = wea_list

    def suggestion_location(self):
        """
        搜索框联想
        """
        res = requests.get(self.current_suggest_api, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36'})
        try:
            res_dict_list = eval(res.text)
        except:
            return []
        return [(res_dict['ref'].split('~')[2] + ' {} '.format(res_dict['ref'].split('~')[-1]) + '-' + res_dict['ref'].split('~')[0]) for res_dict in res_dict_list]

    def set_location(self):
        """
        根据输入的词条联想地点，只有选择联想的词条作为地点搜索才会成功
        ctrl + 上下键可以控制下一个联想
        """
        print(self.input_edit.text())
        if not re.match(r'.+-\d+', self.input_edit.text()):
            self.current_suggest_api = self.suggest_api + self.input_edit.text().split('-')[0]
            # 生成选择
            res_dict_list = self.suggestion_location()
            if len(res_dict_list):
                self.model.setStringList(res_dict_list)
                self.completer.setModel(self.model)

    def update_data(self):
        """
        判断是否匹配为 地点名称 + 代号 格式，如果不是，联想之；是，更新数据
        """
        if not re.match(r'.+-\d+', self.input_edit.text()):
            self.set_location()
        else:
            self.current_weather_api = self.weather_api.format(self.input_edit.text().split('-')[1])
            self.save()
            # 获取天气
            self.get_weather()
            # 初始化数据
            self.init_frame_box()
            self.model.setStringList([])
            self.completer.setModel(self.model)

    def enter_anim(self, obj):
        """
        进入frame出发，上浮动画，阴影渐变动画
        """
        i = obj.property('number')
        self.params[i]['class'] = SeriesAnimation(obj, True, 20, 5, self, i)
        self.params[obj.property('number')]['class'].start()

    def leave_anim(self, obj):
        """
        鼠标离开事件
        """
        i = obj.property('number')
        self.params[i]['class'] = SeriesAnimation(obj, False, 20, 5, self, i)
        self.params[obj.property('number')]['class'].start()

    @staticmethod
    def add_click(obj):
        """
        加号逻辑尚未实现
        """
        print('此按钮纯属摆设')

    def save(self):
        """
        保存词条，在TEMP环境变量中
        """
        with open(self.root, 'w') as f:
            f.write(self.input_edit.text())

    def read(self):
        """
        读取，如果没有，就默认首都
        """
        if not os.path.exists(self.root):
            self.current_weather_api = self.weather_api.format('101010100')
            self.input_edit.setText('北京-101010100')
        else:
            with open(self.root, 'r') as f:
                last_city_code = f.read()
            self.current_weather_api = self.weather_api.format(last_city_code.split('-')[1])
            self.input_edit.setText(last_city_code)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    b = Beauty()
    b.show()
    sys.exit(app.exec())
