import sys
from PySide2 import QtWidgets, QtCore
import pymxs

rt = pymxs.runtime

class BatchRenameWindow(QtWidgets.QWidget):
    def __init__(self):
        super(BatchRenameWindow, self).__init__()
        self.setWindowTitle("Batch Rename Objects")
        self.setFixedSize(300, 220)
        self.setupUI()
    
    def setupUI(self):
        mainLayout = QtWidgets.QVBoxLayout(self)
        
        # Use QFormLayout to align labels and input boxes
        formLayout = QtWidgets.QFormLayout()
        self.findEdit = QtWidgets.QLineEdit()
        self.replaceEdit = QtWidgets.QLineEdit()
        formLayout.addRow("Find:", self.findEdit)
        formLayout.addRow("Replace:", self.replaceEdit)
        mainLayout.addLayout(formLayout)
        
        # Buttons layout: Rename, Exchange, Check
        buttonsLayout = QtWidgets.QHBoxLayout()
        self.renameButton = QtWidgets.QPushButton("Rename Objects")
        self.exchangeButton = QtWidgets.QPushButton("Exchange Strings")
        self.checkButton = QtWidgets.QPushButton("Check")
        buttonsLayout.addWidget(self.renameButton)
        buttonsLayout.addWidget(self.exchangeButton)
        buttonsLayout.addWidget(self.checkButton)
        mainLayout.addLayout(buttonsLayout)
        
        # Result label to show feedback
        self.resultLabel = QtWidgets.QLabel("Matches found:")
        mainLayout.addWidget(self.resultLabel)
        
        # Connect button signals to their slots
        self.renameButton.clicked.connect(self.renameObjects)
        self.exchangeButton.clicked.connect(self.exchangeStrings)
        self.checkButton.clicked.connect(self.checkObjects)
    
    def getObjectsToProcess(self):
        # If any objects are selected, process them; otherwise, process all scene objects.
        return rt.selection if len(rt.selection) > 0 else rt.objects
    
    def renameObjects(self):
        findStr = self.findEdit.text()
        replaceStr = self.replaceEdit.text()
        
        # Validate the find string.
        if findStr == "":
            self.resultLabel.setText("invalid")
            return
        
        objs = self.getObjectsToProcess()
        totalMatches = 0
        for obj in objs:
            totalMatches += obj.name.count(findStr)
        self.resultLabel.setText("Matches found: " + str(totalMatches))
        
        # Perform replacement on each object.
        for obj in objs:
            newName = obj.name.replace(findStr, replaceStr)
            if newName != obj.name:
                obj.name = newName
    
    def checkObjects(self):
        findStr = self.findEdit.text()
        if findStr == "":
            self.resultLabel.setText("invalid find string")
            return
        
        objs = self.getObjectsToProcess()
        totalMatches = 0
        for obj in objs:
            totalMatches += obj.name.count(findStr)
        numObjs = len(objs)
        # Update the result label with the check summary
        self.resultLabel.setText("selected {} objects, found {} matches".format(numObjs, totalMatches))
    
    def exchangeStrings(self):
        temp = self.findEdit.text()
        self.findEdit.setText(self.replaceEdit.text())
        self.replaceEdit.setText(temp)

def main():
    global batchRenameWindow
    try:
        batchRenameWindow.close()
        batchRenameWindow.deleteLater()
    except Exception:
        pass
    batchRenameWindow = BatchRenameWindow()
    batchRenameWindow.show()

if __name__ == "__main__":
    main()
