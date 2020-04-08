# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *

import sys
from configparser import ConfigParser
import logging

from bithumb import Bithumb

from concurrent.futures import ThreadPoolExecutor, as_completed

gui_form = uic.loadUiType('maniBot.ui')[0]

stop_flag = True

logger = get_logger()

def get_logger():
    logger = logging.getLogger("Thread Example")
    logger.setLevel(logging.DEBUG)
    # fh = logging.FileHandler("threading.log") #로그 파일 출력
    fh = logging.StreamHandler()
    fmt = '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    return logger

class Worker(QThread):

    update_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.result = {}

        # Load Config File
        config = ConfigParser()
        config.read('trading.conf')

        connect_key = config.get('ArbBot', 'bithumbKey')
        secret_key = config.get('ArbBot', 'bithumbSecret')
        self.bot = Bithumb(connect_key, secret_key)

    def run(self):
        while True:
            global stop_flag
            if stop_flag == False:
               stop_flag = True
               self.create_thread(5, 3)
               self.update_signal.emit()
            self.msleep(5000)

    def create_thread(self, tot_run, per_run):
        logger.debug('create_thread tot {} per {}' .format(tot_run, per_run))
        mok = tot_run // per_run
        nam = tot_run % per_run
        r= 0
        self.result = {}
        for j in range(1, mok+1):
            start = r
            end = r + per_run
            self.run_thread(start=r, end=end)
            if r >= tot_run:
                break
            r += per_run
        if r <= tot_run:
            self.run_thread(start=r, end=r+nam)

        for k, v in self.result.items():
            print(k, ' :', v)

        self.user_confirm = False

    def run_thread(self, start, end):
        logger.debug("run thread {} ~ {}" .format(start, end))
        futures = {self.executor.submit(self.seek_balance, i): i for i in range(start, end)}
        for future in as_completed(futures):
            try:
                data = future.result()
                # print(data)
            except Exception as ex:
                self.result[future] = 'Fail'
            else:
                self.result[future] = data

    def seek_balance(self, number):
        logger.debug('execute function executing')
        result = self.bot.balance('ETH')
        logger.debug('execute function ended with: {}'.format(number))
        return result

class MyWindow(QMainWindow, gui_form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.MyDialgo()

        self.mode  = 'sell'
        self.auto  = True

        # logger = self.get_logger()
        self.result = []

        self.user_confirm = False

        self.worker = Worker()
        self.worker.update_signal.connect(self.display_result)
        self.worker.start()

    def display_result(self):
        logger.debug('===>display_result')
        self.user_confirm = False

    def MyDialgo(self):

        self.confirm_pushButton.clicked.connect(self.confirm_cmd)
        self.action_pushButton.clicked.connect(self.action_cmd)
        self.refresh_pushButton.clicked.connect(self.refresh_cmd)

        self.sell_radioButton.clicked.connect(self.mode_cmd)
        self.buy_radioButton.clicked.connect(self.mode_cmd)

        self.auto_checkBox.stateChanged.connect(self.auto_cmd)

    def confirm_cmd(self):

        self.user_confirm = False

        price = self.price_lineEdit.text()
        qty   = self.qty_lineEdit.text()
        count = self.count_lineEdit.text()
        # coin  = self.coin_lineEdit.text()
        coin = 'DAC'

        if price == '' or qty == '' or count == '' or coin == '':
            print("Type in parameters")
            self.textBrowser.setText('메시지 : ' + '값을 입력해 주세요')
            return "Error"

        self.price = float(price)
        self.qty   = float(qty)
        self.count = int(count)

        logger.debug("{} @ {} for {}" .format(self.qty, self.price, self.count))
        # display on pannel

        # confirm for user input
        self.user_confirm = True

    def action_cmd(self):
        logger.debug("action_orders_cmd")
        if self.user_confirm :
            # self.create_thread(self.count, 5)
            global stop_flag
            print('stop flag ' , stop_flag)
            stop_flag = False

    def refresh_cmd(self):
        pass

    def mode_cmd(self):
        if self.sell_radioButton.isChecked():
            self.mode = 'sell'
            print('sell')
        elif self.buy_radioButton.isChecked():
            self.mode = 'buy'
            print('buy')
        else:
            raise ValueError

    def auto_cmd(self):
        if self.auto_checkBox.isChecked():
            self.auto = True
        else:
            self.auto = False


def main_QApp():
    app = QApplication(sys.argv)
    main_dialog = MyWindow()
    main_dialog.show()
    app.exec_()


if __name__ == '__main__':
    main_QApp()
