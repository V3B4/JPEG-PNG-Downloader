#!/usr/bin/env python3

import sys
import os
import threading
import requests 
from bs4 import BeautifulSoup 
from time import sleep
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.directory = 0
        self.jpg = 1
        self.png = 1

        self.button = QPushButton("ダウンロード")
        self.button.clicked.connect(self.output)
        self.inputURL = QLineEdit()
        self.inputURL.setText("")
        self.inputDirectory = QLineEdit()
        self.inputDirectory.setText("")

        lineLayout = QGridLayout()
        lineLayout.addWidget(QLabel("URL"), 0, 0)
        lineLayout.addWidget(self.inputURL, 0, 1)
        lineLayout.addWidget(QLabel("保存先"), 1, 0)
        lineLayout.addWidget(self.inputDirectory, 1, 1)
        
        self.cbJPG = QCheckBox('JPG', self)
        self.cbJPG.move(20, 20)
        self.cbJPG.toggle()
        self.cbJPG.stateChanged.connect(self.change_jpg)
        
        self.cbPNG = QCheckBox('PNG', self)
        self.cbPNG.move(20, 20)
        self.cbPNG.toggle()
        self.cbPNG.stateChanged.connect(self.change_png)
        
        exLayout = QGridLayout()
        exLayout.addWidget(self.cbJPG)
        exLayout.addWidget(self.cbPNG)

        self.cbDirectory = QCheckBox('ディレクトリ名を含めて保存(ファイル名が重複する場合など)', self)
        self.cbDirectory.move(20, 20)
        self.cbDirectory.stateChanged.connect(self.change_directory)

        self.status = QLabel(self)
        self.status.setText('準備完了')

        layout = QVBoxLayout()
        layout.addLayout(lineLayout)
        layout.addLayout(exLayout)
        layout.addWidget(self.cbDirectory)
        layout.addWidget(self.button)
        layout.addWidget(self.status)

        self.setLayout(layout)
        self.setWindowTitle("図片下載工具 Ver1.0.1")
        self.resize(400, 150)

    def change_directory(self, state):
        if state == Qt.Checked:
            self.directory = 1
        else:
            self.directory = 0
    
    def change_jpg(self, state):
        if state == Qt.Checked:
            self.jpg = 1
        else:
            self.jpg = 0
    
    def change_png(self, state):
        if state == Qt.Checked:
            self.png = 1
        else:
            self.png = 0

    def output(self):
        self.button.setEnabled(False)
        self.status.setText('ダウンロード開始')
        self.url = self.inputURL.text()
        self.place = self.inputDirectory.text()
        self.extensions = []
        if self.jpg == 1:
            self.extensions.extend(["jpg", "JPG", "jpeg", "JPEG"])
        if self.png == 1:
            self.extensions.extend(["png", "PNG"])

        thread = threading.Thread(target=self.run)
        thread.start()

    def run(self):
        place = self.place
        url = self.url
        extensions = self.extensions
        directory = self.directory

        def delete_directory(name):
            names = name.split('/')
            return names[len(names) - 1]
        def download(url, name, directory, place):
            if directory == 0:
                name = delete_directory(name)
            if directory == 1:
                name = name.replace('/', '_')
            name = place + name
            self.status.setText('ダウンロード中 '+ str(self.count+1) + '/' + str(self.len_images) + ' ' + name)
            req = requests.get(url)
            if req.status_code == 200:
                with open(name, 'wb') as f:
                    f.write(req.content)

        if place != "":
            if place[-1:] != "/":
                place = place + "/"
        os.makedirs(place[:-1], exist_ok=True)

        links = [] 
        soup = BeautifulSoup(requests.get(url).content,'lxml')
        for link in soup.find_all("img"):
            l = link.get("src")
            if l is not None:
                links.append(l)
        for link in soup.find_all("a"):
            l = link.get("href")
            if l is not None:
                links.append(l)
            
        images = []
        for link in links:
            if link[-3:] in extensions:
                images.append(link)

        if url[-4:] in ["html", ".htm"]:
            i = 0                # URLの後ろから/までを削除
            for x in url[::-1]:
                if x == "/":
                    break
                i += 1
            url_dl = url[:i*-1] # 相対パス用のアドレス
                                # http:〜/ + image1.jpg のように連結
        elif url[-1:] == "/":
            url_dl = url        # /が付いている場合
        else:
            url_dl = url + "/"  # /を追加

        self.len_images = len(images)
        for self.count, image in enumerate(images):
            sleep(1)
            if image[:2] == "./": # ./対策
                image = image[2:]

            # 絶対パスの場合
            if image[:4] == "http": 
                i = 0
                n = 0
                for x in image:
                    i += 1
                    if x == "/":
                        if n == 1:
                            break
                        n += 1
                download(image, image[i:], directory, place)

            # ../が含まれている場合
            elif image[:3] == "../": 
                url_cut = url_dl
                while image[:3] == "../":
                    i = 0
                    for x in url_cut[:-1][::-1]:
                        i += 1
                        if x == "/":
                            break
                    url_cut = url_cut[:i*-1] # 1ディレクト分削除したURL
                    image = image[3:]

                download(url_cut + image, image[i:], directory, place)

            else:
                download(url_dl + image, image, directory, place) 
        self.status.setText('ダウンロード完了')
        self.button.setEnabled(True)

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

def gui_main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icon.ico')))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    gui_main()
