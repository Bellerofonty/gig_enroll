import sys
import time
import requests
import json
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, pyqtSignal

import gig_widget


class GigScan(QThread):
    '''Циклический поиск поста с записью на тренировку (отдельный поток)'''
    result_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    success_signal = pyqtSignal()

    def __init__(self, parent = None, delay = 5):
        QThread.__init__(self, parent)
        self.delay = delay

    def run(self):
        '''Получает последний комментарий в теме по номеру, взятому с запасом.
        По его номеру минус n получает следующие values['count']=40 комментариев
        с периодичностью delay, полученной из gui. Сканирует их, сигнализирует
        в gui о результатах.
        '''
        url = 'https://api.vk.com/method/board.getComments?'
        with open('values.txt', 'r', encoding='utf-8') as f:
            values = json.load(f)    # Данные запроса из файла

        # Получение номера последнего комментария в теме
        values['start_comment_id'] = 1000000
        res = requests.get(url, params=values)
        d = json.loads(res.text)
        # n - Поправка на случай, когда новых комментариев несколько
        n = 10
        values['start_comment_id'] = d['response']['real_offset'] - n
##        values['start_comment_id'] = 16122
        enroll = 0
        while not enroll:   # Поиск, пока не найден пост с записью
            res = requests.get(url, params=values)
            d = json.loads(res.text)

            for i in d['response']['items']:
                if i['from_id'] == -10916742:
                    if 'чебный выход' or 'Запись в этой теме' in i['text']:
                        enroll = 1

            tm = time.strftime("%H:%M:%S",time.localtime())
            if enroll:
                is_enroll = 'ЗАПИСЬ ЕСТЬ'
                self.success_signal.emit()
            else:
                is_enroll = 'Нет записи'
            new_result = tm + ' ' + is_enroll + '\n'
            self.result_signal.emit(new_result)

            if not enroll:
                for i in range(1, 101): # Обновление индикатора времени ожидания
                    time.sleep(0.01 * self.delay)
                    self.progress_signal.emit(i)


class GigApp(QtWidgets.QWidget, gig_widget.Ui_Form):
    '''GUI и управление потоком поиска'''
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_start.clicked.connect(self.start_scan)
        self.btn_stop.clicked.connect(self.stop_scan)
        self.thread = GigScan() # Поиск в отдельном потоке
        self.thread.result_signal.connect(self.show_result)
        self.thread.started.connect(self.on_started)
        self.thread.finished.connect(self.on_finished)
        self.thread.progress_signal.connect(self.show_progress)
        self.thread.success_signal.connect(self.success_alarm)

    def start_scan(self):
        # Выбор задержки между запросами в секундах
        if self.radioButton.isChecked():
            self.thread.delay = 60
        elif self.radioButton_2.isChecked():
            self.thread.delay = 120
        elif self.radioButton_3.isChecked():
            self.thread.delay = 300
        elif self.radioButton_4.isChecked():
            self.thread.delay = 600
        self.btn_stop.setEnabled(True)
        self.thread.start()

    def stop_scan(self):
        self.thread.terminate()
        self.on_finished()

    def show_result(self, result):
        '''Добавляет запись в лог и проматывает его вниз'''
        self.log.textCursor().insertText(result)
        self.log.ensureCursorVisible()

    def on_started(self):
        self.btn_start.setDisabled(True)

    def on_finished(self):
        self.btn_start.setDisabled(False)
        self.btn_stop.setDisabled(True)
        self.progressBar.reset()

    def show_progress(self, progress):
        self.progressBar.setValue(progress)

    def success_alarm(self):
        '''Окно меняет цвет фона, разворачивается, всплывает'''
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor('#9ACD32'))
        self.setPalette(pal)
        self.showNormal()
        self.activateWindow()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = GigApp()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()