import subprocess, shlex, sys, re, datetime
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtGui
from PyQt4 import QtCore
from pymongo import Connection
from pymongo import MongoClient
from time import strftime

class mainForm(QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        global db, collection, status

        connection = Connection('localhost', 27017)
        db = connection.diary
        collection = db.tasks

        self.setGeometry(300, 300, 500, 400)
        self.setWindowTitle('Мои задачи')

        self.myTaskList = QtGui.QTableView(self)
        self.model = QStandardItemModel()
        self.myTaskList.setGeometry(10, 50, 480, 270)

        createTaskButton = QtGui.QPushButton('Новая задача',self)
        self.viewTaskButton = QtGui.QPushButton('Просмотр',self)
        settingsButton = QtGui.QPushButton('Параметры',self)

        self.activeTaskButton = QtGui.QPushButton('Активные задачи',self)
        self.doneTaskButton = QtGui.QPushButton('Выполненные задачи',self)

        createTaskButton.setGeometry(10, 325, 100, 70)
        self.viewTaskButton.setGeometry(130, 325, 100, 70)
        settingsButton.setGeometry(390, 360, 100, 35)       

        self.activeTaskButton.setGeometry(30, 10, 190, 35)
        self.doneTaskButton.setGeometry(280, 10, 190, 35)

        status = 'active'
        self.getTasklist(status)
        self.activeTaskButton.setEnabled(False)
        self.viewTaskButton.setEnabled(False)

        self.activeTaskButton.clicked.connect(lambda: self.getTasklist('active'))
        self.doneTaskButton.clicked.connect(lambda: self.getTasklist('done'))
        createTaskButton.clicked.connect(lambda: self.addNewTask())
        self.viewTaskButton.clicked.connect(lambda: self.viewTaskDetails(selectedValue))
        self.connect(self.myTaskList, QtCore.SIGNAL("clicked(QModelIndex)"), self.valueSelected)
        settingsButton.clicked.connect(lambda: self.openSettings())

    def valueSelected(self, index):

        global selectedValue
        
        valueModel = self.myTaskList.model()
        self.viewTaskButton.setEnabled(True)
        valueIndex = valueModel.index(index.row(), 0)
        selectedValue = valueModel.data(valueIndex)

    def getTasklist(self, status):
        self.model.clear()
        if status == 'active':
            self.model.setColumnCount(3)
            self.model.setHorizontalHeaderLabels(("Наименование задачи;Срок исполнения;До веремени").split(";"))
            self.activeTaskButton.setEnabled(False)
            self.doneTaskButton.setEnabled(True)
            for task in collection.find({'task_status' : status}):
                row = []
                item = QStandardItem(task['taskname'])
                item.setEditable(False)
                row.append(item)
                try:
                    task['deadline_date']
                except KeyError:
                    task['deadline_date'] = '-'
                    task['deadline_time'] = '-'
                item = QStandardItem(task['deadline_date'])
                item.setEditable(False)
                row.append(item)
                item = QStandardItem(task['deadline_time'])
                item.setEditable(False)
                row.append(item)
                self.model.appendRow(row)
            self.myTaskList.setColumnWidth(0, 263)
            self.myTaskList.setColumnWidth(1, 110)
            self.myTaskList.setColumnWidth(2, 90)
            self.myTaskList.setModel(self.model)
        else:
            self.model.setColumnCount(3)
            self.model.setHorizontalHeaderLabels(("Наименование задачи;Дата закрытия;Время закрытия").split(";"))
            self.activeTaskButton.setEnabled(True)
            self.doneTaskButton.setEnabled(False)
            self.myTaskList.setColumnWidth(0, 263)
            self.myTaskList.setColumnWidth(1, 100)
            self.myTaskList.setColumnWidth(2, 100)

            for task in collection.find({'task_status' : status}).sort([('_id', -1)]):
                row = []
                item = QStandardItem(task['taskname'])
                item.setEditable(False)
                row.append(item)
                item = QStandardItem(task['done_date'])
                item.setEditable(False)
                row.append(item)
                item = QStandardItem(task['done_time'])
                item.setEditable(False)
                row.append(item)
                self.model.appendRow(row)
                self.myTaskList.setModel(self.model)
                
    def addNewTask(self):
        self.ntsk = newTaskWindow()
        self.ntsk.show()

    def openSettings(self):
        self.sett = settingsDialog()
        self.sett.show()

    def viewTaskDetails(self, selectedValue):
        self.tdtl = taskDetailsWindow()
        self.tdtl.show()

class newTaskWindow(QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 500, 400)
        self.setWindowTitle('Новая задача')

        taskNameLabel = QtGui.QLabel('Наименование задачи:', self)
        taskNameLabel.setGeometry(10, 10, 120, 20)

        descriptionLabel = QtGui.QLabel('Описание задачи:', self)
        descriptionLabel.setGeometry(10, 40, 100, 20)

        taskDateTimeLabel = QtGui.QLabel('Указать сроки исполнения:', self)
        taskDateTimeLabel.setGeometry(290, 330, 150, 20)

        dateLabel = QtGui.QLabel('Дата:', self)
        timeLabel = QtGui.QLabel('Время:', self)

        dateLabel.setGeometry(220, 360, 40, 20)
        timeLabel.setGeometry(360, 360, 40, 20)

        self.taskName = QtGui.QLineEdit(self)
        self.taskName.setGeometry(145, 10, 340, 25)

        self.descriptionField = QtGui.QTextEdit(self)
        self.descriptionField.setGeometry(10, 70, 480, 250)

        applyButton = QtGui.QPushButton('Добавить', self)
        applyButton.setGeometry(10, 340, 70, 50)
        applyButton.clicked.connect(lambda: self.addTask())

        self.taskDate = QtGui.QDateEdit(self)
        self.taskDate.setDateTime(QtCore.QDateTime.currentDateTime())
        self.taskDate.setGeometry(260, 360, 90, 20)

        self.taskTime = QtGui.QTimeEdit(self)
        self.taskTime.setGeometry(400, 360, 90, 20)

        self.dateTimeEnable = QtGui.QCheckBox(self)
        self.dateTimeEnable.setChecked(False)
        self.dateTimeEnable.move(270, 325)

        self.dateTimeEnable.stateChanged.connect(self.enableDateTime)

        self.taskDate.setEnabled(False)
        self.taskTime.setEnabled(False)
                
    def enableDateTime(self, stat):
        if stat == 2:
            self.taskDate.setEnabled(True)
            self.taskTime.setEnabled(True)
        else:
            self.taskDate.setEnabled(False)
            self.taskTime.setEnabled(False)

    def addTask(self):
        if self.taskName.text() != '':
            if self.dateTimeEnable.checkState() == 2:
                db.tasks.insert({'taskname' : self.taskName.text(), 'description' : self.descriptionField.toPlainText(), 'deadline_date' : self.taskDate.text(), 'deadline_time' : self.taskTime.text(), 'task_status' : "active", 'comments' : []})
            else:
                db.tasks.insert({'taskname' : self.taskName.text(), 'description' : self.descriptionField.toPlainText(), 'task_status' : "active", 'comments' : []})
            self.close()
        else:
            QMessageBox.information(self, 'Ошибка', 'Введите наименование задачи', QMessageBox.Ok)

class settingsDialog(QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(430, 300, 300, 400)
        self.setWindowTitle('Параметры')

class taskDetailsWindow(QMainWindow):   
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.setGeometry(300, 300, 500, 400)
        self.setWindowTitle('Хронология выполнения задачи')

        for task in collection.find({'taskname':selectedValue}):
            descriptionInfo = task['description']
            try:
                datetimeInfo = task['deadline_date'] + ' ' + task['deadline_time']
            except KeyError:
                datetimeInfo = '-'

        self.myCommentsList = QtGui.QTableView(self)
        self.model = QStandardItemModel()
        self.myCommentsList.setGeometry(10, 100, 480, 210)

        self.model.clear()
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderLabels(("Дата;Комментарий").split(";"))

        self.reportButton = QtGui.QPushButton('Отчёт',self)
        self.reportButton.setGeometry(390, 360, 100, 35)
        self.reportButton.setVisible(False)
             
        taskNameLabel = QtGui.QLabel('Наименование задачи:', self)
        descriptionLabel = QtGui.QLabel('Описание задачи:', self)
        datetimeLabel = QtGui.QLabel('Срок исполнения:', self)

        taskNameLabelInfo = QtGui.QLabel(selectedValue, self)
        descriptionLabelInfo = QtGui.QLabel(descriptionInfo, self)
        datetimeLabelInfo = QtGui.QLabel(datetimeInfo, self)

        taskNameLabel.setGeometry(10, 10, 120, 20)
        descriptionLabel.setGeometry(10, 40, 100, 20)
        datetimeLabel.setGeometry(10, 70, 100, 20)

        taskNameLabelInfo.setGeometry(130, 10, 120, 20)
        descriptionLabelInfo.setGeometry(110, 40, 370, 20)
        datetimeLabelInfo.setGeometry(110, 70, 100, 20)
        
        self.commentField = QtGui.QTextEdit(self)
        self.commentField.setGeometry(10, 315, 480, 40)

        self.commitButton = QtGui.QPushButton('Комментировать', self)
        self.closeTaskButton = QtGui.QPushButton('Закрыть задачу', self)
        
        self.commitButton.setGeometry(390, 360, 100, 35)
        self.closeTaskButton.setGeometry(10, 360, 100, 35)

        if task['task_status'] == 'done':
            self.commitButton.setVisible(False)
            self.commentField.setVisible(False)
            self.closeTaskButton.setVisible(False)
            self.reportButton.setVisible(True)
       
        for comm in collection.find({'taskname' : selectedValue}, {"comments" : 1}):
            if len(comm) > 1:
                for comment in comm['comments']:
                    row = []
                    comment = str(comment)
                    result = re.findall(r"([^']*)", comment)
                    if result:
                        item = QStandardItem(result[2])
                        item.setEditable(False)
                        row.append(item)
                        item = QStandardItem(result[6])
                        item.setEditable(False)
                        row.append(item)
                        self.model.appendRow(row)
                    self.myCommentsList.setModel(self.model)

        self.commitButton.clicked.connect(lambda: self.addComment())
        self.closeTaskButton.clicked.connect(lambda: self.closeTask())

    def addComment(self):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment = self.commentField.toPlainText()
        if comment != '':
            collection.update({'taskname' : selectedValue},{'$push' : {'comments' : {timestamp : comment}}})
            self.commentField.setText('')

    def closeTask(self):
        dialogResult = QMessageBox.question(self, 'Подтверждение закрытия', 'Закрыть задачу?', QMessageBox.Yes, QMessageBox.No)
        if dialogResult == QMessageBox.Yes:
            dateStamp = datetime.datetime.now().strftime('%Y-%m-%d')
            timeStamp = datetime.datetime.now().strftime('%H:%M:%S')
            collection.update({'taskname' : selectedValue}, {'$set' : {'task_status' : "done", 'done_date' : dateStamp, 'done_time' : timeStamp}})
        self.close()

if __name__ == "__main__":
    cmd = 'C:\\Program Files\\MongoDB 2.6 Standard\\bin\\mongod.exe'
    activeMongo = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    app = QApplication(sys.argv)
    form = mainForm()
    form.show()
    app.exec_()
