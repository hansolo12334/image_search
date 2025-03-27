# coding:utf-8
from PyQt5.QtCore import Qt, QPoint,QThread,pyqtSignal,pyqtSlot,QTimer,QEvent,QUrl
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget, QHBoxLayout


from qfluentwidgets import SearchLineEdit,PushButton,StrongBodyLabel




from pathlib import Path
import os

class LineEdit(SearchLineEdit):
  """ Search line edit """
    

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setPlaceholderText(self.tr('Search icons'))
    self.setFixedWidth(304)
    # self.textChanged.connect(self.search)
    
    self.returnPressed.connect(self.search)
    
    
    
class TagButton(PushButton):
  button_delete=pyqtSignal(PushButton)
  def __init__(self, parent: QWidget = None):
    super().__init__(parent)
    
    self.SELECTED_STATE=0 #0 包含  1 排除
    self.selected_state_changed=False
    self.delete_button_timer=QTimer(interval=800, timeout=self.exclude_button, singleShot=True)
    
  def mousePressEvent(self, e):
    # button = e.button()
    # if button == Qt.LeftButton:
    #   self.SELECTED_STATE=self.SELECTED_STATE+1
    #   if(self.SELECTED_STATE>3):
    #     self.SELECTED_STATE=0
      
    # if button == Qt.RightButton:
    #   self.SELECTED_STATE=self.SELECTED_STATE-1
    #   if(self.SELECTED_STATE<0):
    #     self.SELECTED_STATE=0
    self.selected_state_changed=False
    self.delete_button_timer.start()

    super().mousePressEvent(e)
  
  def mouseReleaseEvent(self, e):
    if self.selected_state_changed is False:
      
      self.button_delete.emit(self) 
    super().mouseReleaseEvent(e)
   
   
  def exclude_button(self):
    if self.isPressed is True:
      if self.SELECTED_STATE != 1:
        print("排除")
        self.SELECTED_STATE=1
        font=self.font()
        font.setStrikeOut(True)
        self.setFont(font)
      else:
        print("包含")
        self.SELECTED_STATE=0
        font=self.font()
        font.setStrikeOut(False)
        self.setFont(font)
        
      self.selected_state_changed=True

class ExampleCard(QWidget):
    """ Example card """

    def __init__(self, title, widget: QWidget, stretch=0, parent=None):
        super().__init__(parent=parent)
        self.widget = widget
        self.stretch = stretch

        self.titleLabel = StrongBodyLabel(title, self)
        self.card = QFrame(self)

        self.sourceWidget = QFrame(self.card)
        # self.sourcePath = sourcePath
        # self.sourcePathLabel = BodyLabel(
        #     self.tr('Source code'), self.sourceWidget)
        # self.linkIcon = IconWidget(FluentIcon.LINK, self.sourceWidget)

        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = QVBoxLayout(self.card)
        self.topLayout = QHBoxLayout()
        self.bottomLayout = QHBoxLayout(self.sourceWidget)

        self.__initWidget()

    def __initWidget(self):
        # self.linkIcon.setFixedSize(16, 16)
        self.__initLayout()

        # self.sourceWidget.setCursor(Qt.PointingHandCursor)
        # self.sourceWidget.installEventFilter(self)

        self.card.setObjectName('card')
        # self.sourceWidget.setObjectName('sourceWidget')

    def __initLayout(self):
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.cardLayout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.topLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)

        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.setContentsMargins(12, 12, 12, 12)
        self.bottomLayout.setContentsMargins(18, 18, 18, 18)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)

        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.card, 0, Qt.AlignTop)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.cardLayout.setSpacing(0)
        self.cardLayout.setAlignment(Qt.AlignTop)
        self.cardLayout.addLayout(self.topLayout, 0)
        self.cardLayout.addWidget(self.sourceWidget, 0, Qt.AlignBottom)

        self.widget.setParent(self.card)
        self.topLayout.addWidget(self.widget)
        if self.stretch == 0:
            self.topLayout.addStretch(1)

        self.widget.show()

        # self.bottomLayout.addWidget(self.sourcePathLabel, 0, Qt.AlignLeft)
        # self.bottomLayout.addStretch(1)
        # self.bottomLayout.addWidget(self.linkIcon, 0, Qt.AlignRight)
        # self.bottomLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    # def eventFilter(self, obj, e):
    #     if obj is self.sourceWidget:
    #         if e.type() == QEvent.MouseButtonRelease:
    #             QDesktopServices.openUrl(QUrl(self.sourcePath))

    #     return super().eventFilter(obj, e)