import sys
import time
import requests
import json
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal

import gig_widget

##print(time.ctime(1365439969))
##print(time.time())


##class Delay(QThread):
####    def __init__(self):
####        super.__init__(self)
##
##    def run(self):
####        pass
##        time.sleep(5)
##        print('hello')

class GigScan(QThread):
    '''Циклический поиск поста с записью на тренировку (отдельный поток)'''
    result_signal = pyqtSignal(str)
##    window.btn_stop.clicked.connect(QThread.yieldCurrentThread())

    def __init__(self, parent = None, delay = 5):
        QThread.__init__(self, parent)
        self.delay = delay

    def run(self):
        url = 'https://api.vk.com/method/board.getComments?'
        with open('values.txt', 'r', encoding='utf-8') as f:
            values = json.load(f)

        enroll = 0
        while not enroll:   # Поиск, пока не найден пост с записью
            res = requests.get(url, params=values)
            d = json.loads(res.text)

            for i in d['response']['items']:
                if i['from_id'] == -10916742:
        ##            print('>>', i['text'], '\n')
                    if 'состоится учебный выход' in i['text']:
                        enroll = 1

            tm = time.strftime("%H:%M:%S",time.localtime())
            if enroll:
##                print(tm, 'ЗАПИСЬ ЕСТЬ')
                is_enroll = 'ЗАПИСЬ ЕСТЬ'
            else:
##                print(tm, 'Нет записи')
                is_enroll = 'Нет записи'
            self.result_signal.emit(tm+' '+is_enroll)

        ##    print('_______________')
            time.sleep(self.delay)
            values['start_comment_id'] -= 1


class GigApp(QtWidgets.QWidget, gig_widget.Ui_Form):
    '''GUI и управление потоком поиска'''
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_start.clicked.connect(self.start_scan)
        self.btn_stop.clicked.connect(self.stop_scan)
        self.thread = GigScan()
        self.thread.result_signal.connect(self.show_result)
        self.thread.started.connect(self.on_started)
        self.thread.finished.connect(self.on_finished)

    def start_scan(self):
        if self.radioButton.isChecked():
            self.thread.delay = 1
        elif self.radioButton_2.isChecked():
            self.thread.delay = 2
        elif self.radioButton_3.isChecked():
            self.thread.delay = 5
        elif self.radioButton_4.isChecked():
            self.thread.delay = 10
        self.btn_stop.setEnabled(True)
        self.thread.start()

    def stop_scan(self):
        self.thread.terminate()
        self.on_finished()

    def show_result(self, result):
        self.label.setText(result)

    def on_started(self):
        self.btn_start.setDisabled(True)

    def on_finished(self):
        self.btn_start.setDisabled(False)
        self.btn_stop.setDisabled(True)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = GigApp()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()