# coding:utf-8
from PyQt5.QtCore import Qt, QPoint,QThread,pyqtSignal,QTimer,QEvent,QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices,QFontMetrics
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget, QHBoxLayout


from qfluentwidgets import SmoothScrollArea, FlowLayout, TextWrap, SingleDirectionScrollArea,ImageLabel,SearchLineEdit,CommandBarView,Action,Flyout,FlyoutAnimationType,PushButton,StrongBodyLabel,IconWidget,FluentIcon

from qfluentwidgets import FluentIcon as FIF

from .image_gallery_interface import ImageGalleryInterface
from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..common.translator import Translator

from pathlib import Path
import os
from queue import Queue


class LineEdit(SearchLineEdit):
    """ Search line edit """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(self.tr('Search icons'))
        self.setFixedWidth(304)
        self.textChanged.connect(self.search)



class TagButton(PushButton):
  button_delete=pyqtSignal(bool)
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
      print("删除按钮")
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
  
   
   
   
class ImageSourceLoaderThread(QThread):
  imageLoaded=pyqtSignal(list)
  finished=pyqtSignal()
  
  def __init__(self, folder_path,recur=True):
     super().__init__()
     self.folder_path=folder_path
     self.recur=recur
     
     
  def run(self):
    image_files=self.search_image(self.folder_path,self.recur)
    self.imageLoaded.emit(image_files)
    self.finished.emit()
  
  
  def search_image(self,folder_path,recur=False)-> list:
    image_files = []
    idx=0
    if recur:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                  file_path=Path(os.path.join(root, file)).as_posix()
                  image_files.append((idx,file , file_path))
                  idx=idx+1
                # image_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
              file_path=Path(os.path.join(folder_path, file)).as_posix()
              image_files.append((idx,file , file_path))
              idx=idx+1
              
    return image_files


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

class ImageCard(QFrame):
  imageCardClicked=pyqtSignal(QPoint)
  def __init__(self, path,filename,parent = None):
    super().__init__(parent=parent)
    
    self.maxTextWidth=110 #180
    self.maxCardWidth=150 #220
    
    self.setFixedSize(self.maxCardWidth, self.maxCardWidth)
    self.image_path=path
    self.image_name=filename
    self.imageWidget = QWidget(self)
    # self.image_label=ImageLabel(self)
    self.imageLabel=ImageLabel(self)
    self.imageNameLable=QLabel(self)
    self.isImageLoaded = False  # 标记图片是否加载
    
    self.__initWidget()
  
  def __initWidget(self):
    
    self.setCursor(Qt.PointingHandCursor)
    
    # if self.image_path is not None:
    #   self.imageLabel=ImageLabel(QPixmap(self.image_path).scaled(self.maxTextWidth, self.maxTextWidth,Qt.KeepAspectRatio),self)
    # else:
    #   self.imageLabel=ImageLabel(QPixmap(self.maxTextWidth, self.maxTextWidth),self)
    
    font_metrics = QFontMetrics(self.imageNameLable.font())
    elided_text = font_metrics.elidedText(self.image_name, Qt.ElideRight, self.maxTextWidth)
    self.imageNameLable.setText(elided_text)
    self.imageNameLable.setWordWrap(False)  # 禁止换行
        
    self.imageWidget.setFixedSize(self.maxTextWidth, self.maxTextWidth)
    self.imageWidgetLayOut=QVBoxLayout(self.imageWidget)
    self.imageWidgetLayOut.addWidget(self.imageLabel, 0, Qt.AlignHCenter)
    
    self.vBoxLayout = QVBoxLayout(self)
    # self.vBoxLayout.setSpacing(0)
    # self.vBoxLayout.setContentsMargins(10, 1, 10, 1)
    self.vBoxLayout.addWidget(self.imageWidget)

    self.vBoxLayout.addSpacing(5)
    self.vBoxLayout.addWidget(self.imageNameLable, 0, Qt.AlignHCenter)

    self.imageNameLable.setObjectName("imageNameLable")
    
    # self.imageLabel.clicked.connect(self.computClickedPos)
    
    
  # def mouseReleaseEvent(self, e):
  #   super().mouseReleaseEvent(e)
  #   print(self.image_path)
  
  def mousePressEvent(self, e):
    super().mousePressEvent(e)
    
    print(self.image_path)
    self.computClickedPos()
    
    
  def set_image(self,index):
    if self.isImageLoaded:
      return 
 
    pixmap=QPixmap(self.image_path).scaled(self.maxTextWidth, self.maxTextWidth,Qt.KeepAspectRatio)
    self.imageLabel.setPixmap(pixmap)
    self.isImageLoaded=True
    
    # print(f"加载图片 {index}")
    # self.imageWidgetLayOut.setAlignment(Qt.AlignHCenter)
    self.imageWidgetLayOut.update()
    self.update()


  def computClickedPos(self):

    x = self.imageLabel.width()
    pos = self.imageLabel.mapToGlobal(QPoint(x, 0))
    print(pos.x(),pos.y())
    self.imageCardClicked.emit(pos)
    # Flyout.make(view, pos, self, FlyoutAnimationType.FADE_IN)
    
class ImageCardView(QWidget):
  
  def __init__(self, parent=None):
    
    super().__init__(parent)
    
    self.searchLineEdit = LineEdit(self)
    
    self.view = QFrame(self)
    self.scrollArea = SmoothScrollArea(self.view)
    self.scrollWidget = QWidget(self.scrollArea)
    
    self.vBoxLayout = QVBoxLayout(self)
    self.hBoxLayout = QHBoxLayout(self.view)
    self.flowLayout = FlowLayout(self.scrollWidget, isTight=True)
    
    self.image_data = []  # 存储所有图片路径和文件名 = [] 
    self.currentIndex = -1
    self.allCards: list[ImageCard] = []
    self.cards_infos = []
    self.card_width=150
    self.card_height=150
    self.cards_per_row = 0  # 每行卡片数
     
    self.max_cards_per_chunk=25 #每段最大加载的图片数量 54 15
    self.loaded_chunks_size=0
    self.loaded_cards_num=0
    
    
    self.tagButtons: list[TagButton]=[]
    
    self.loadImageLazy=True #是否懒加载
     # 添加懒加载相关
    self.imageQueue = []  # 待加载图片队列
    self.loadTimer = QTimer(interval=25, timeout=self.loadImage, singleShot=True) #25
    self.lazyTimer = QTimer(interval=100, timeout=self.lazyLoadImage, singleShot=True)#100
    self.lazyIndex = 0  # 用于延迟加载的索引
        
    self.__initWidget()
     
  def __initWidget(self):
    self.scrollArea.setWidget(self.scrollWidget)
    self.scrollArea.setViewportMargins(0, 5, 0, 5)
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
    self.vBoxLayout.setSpacing(12)
    self.vBoxLayout.addWidget(self.searchLineEdit)
    
 
    self.tagCard = ExampleCard(self.tr('标签'), self.createWidget(), stretch=1)
    self.vBoxLayout.addWidget(self.tagCard, 0, Qt.AlignTop)
   
      
      
    self.vBoxLayout.addWidget(self.view)
    self.hBoxLayout.setSpacing(0)
    self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
    self.hBoxLayout.addWidget(self.scrollArea)
    
    self.flowLayout.setVerticalSpacing(8)
    self.flowLayout.setHorizontalSpacing(8)
    self.flowLayout.setContentsMargins(8, 3, 8, 8)
    
   

    self.__setQss()
    cfg.themeChanged.connect(self.__setQss)
    
    self.searchLineEdit.clearSignal.connect(self.showAllImages)
    self.searchLineEdit.searchSignal.connect(self.search)
    
    
    self.scrollArea.verticalScrollBar().valueChanged.connect(self.updataVisableCards)
    self.scrollArea.resizeEvent=self.onScrollAreaResized
  
  
  def createWidget(self, animation=False):
    texts = [
        self.tr('Star Platinum'), self.tr('Hierophant Green'),
        self.tr('Silver Chariot'), self.tr('Crazy diamond'),
        self.tr("Heaven's Door"), self.tr('Killer Queen'),
        self.tr("Gold Experience"), self.tr('Sticky Fingers'),
        self.tr("Sex Pistols"), self.tr('Dirty Deeds Done Dirt Cheap'),
    ]

    widget = QWidget()
    layout = FlowLayout(widget, animation)

    layout.setContentsMargins(0, 0, 0, 0)
    layout.setVerticalSpacing(20)
    layout.setHorizontalSpacing(10)

    for text in texts:
      tagbutton=TagButton(text)
      self.tagButtons.append(tagbutton)
      layout.addWidget(tagbutton)
    return widget
  
  def loadImage(self):
    """从队列中加载图片"""
    if len(self.imageQueue)==0:
        return
    idx = self.imageQueue.pop(0)  # 从队列头部取卡片
    self.allCards[idx].set_image(idx)
    if self.imageQueue:
        self.loadTimer.start()
    else:
        self.lazyTimer.start()

  def lazyLoadImage(self):
    """延迟加载剩余卡片"""
    self.lazyIndex += 1
    if self.lazyIndex >= len(self.image_data):
        return
    if self.lazyIndex in self.cards_infos:
        card = self.allCards[self.lazyIndex]
        if not card.isImageLoaded:
            card.set_image(self.lazyIndex)
    # 继续延迟加载
    if not self.imageQueue:
        self.lazyTimer.start()
            
  def onScrollAreaResized(self,event):
    super(SmoothScrollArea,self.scrollArea).resizeEvent(event)
    self.updateContentSize()
    self.updataVisableCards()
   
  
  def updateContentSize(self):
      if self.loaded_cards_num==0:
          self.scrollWidget.setFixedHeight(0)
          return
      viewport_width = self.scrollArea.viewport().width()
      self.cards_per_row = max(1, viewport_width // (self.card_width + 8))
      total_rows = (self.loaded_cards_num + self.cards_per_row - 1) // self.cards_per_row
      total_height = total_rows * (self.card_height + 8) + 3 + 8  # 包括间距和边距
      self.scrollWidget.setFixedHeight(total_height)
      
      self.scrollWidget.updateGeometry()
      self.flowLayout._doLayout(self.scrollArea.rect(),True)
      self.scrollArea.update()
      QTimer.singleShot(0, lambda: self.flowLayout._doLayout(self.scrollWidget.rect(), True))
      
  def loadVisableCards(self,start_idx,end_idx):
    # print(f"加载图片 {start_idx}~{end_idx}")
    for idx in range(start_idx,end_idx):
      # pass
      self.imageQueue.append(idx)
      # self.allCards[idx].set_image(idx)
    if len(self.imageQueue)!=0 and not self.loadTimer.isActive():
            self.loadTimer.start()
            
            
            
  def updataVisableCards(self):
    if len(self.image_data)==0:
      return
    
    # print(self.loaded_cards_num)
    
    # viewport_height = self.scrollArea.viewport().height()
    # scroll_pos = self.scrollArea.verticalScrollBar().value()

    # visible_rows = max(1, (viewport_height + self.card_height - 1) // (self.card_height + 8))
    # start_row = max(0, scroll_pos // (self.card_height + 8))
    # start_index = start_row * self.cards_per_row
    # end_index = min(len(self.image_data)-1, (start_row + visible_rows + 1) * self.cards_per_row)  # 多加载一行缓冲

    # print("视窗值:",start_index,' ',end_index)
    
    # if(self.loaded_chunks_size*self.max_cards_per_chunk<end_index) and self.loaded_cards_num<=len(self.image_data):
    if self.scrollArea.verticalScrollBar().value()>self.scrollArea.verticalScrollBar().maximum()*0.95 and self.loaded_cards_num<len(self.image_data):
      # print("向后加载chunk")
      self.load_card_chunk()
      self.updateContentSize()
 
    
  
  
  
  def addIcon(self, idx,image_path,filename):
    card=ImageCard(image_path,filename)
    
    card.imageCardClicked.connect(self.createCommandBarFlyout)
    if not self.loadImageLazy:
      card.set_image(idx)
    self.cards_infos.append((idx,image_path,filename))
    self.allCards.append(card)
    self.flowLayout.addWidget(card)
    
  def __setQss(self):
    self.view.setObjectName('imageView')
    self.scrollWidget.setObjectName('scrollWidget')
    self.scrollArea.setObjectName("scrollArea")
    
    
    StyleSheet.IMAGE_INTERFACE.apply(self)
    StyleSheet.IMAGE_INTERFACE.apply(self.scrollWidget)
    StyleSheet.IMAGE_INTERFACE.apply(self.scrollArea)
     
    if self.currentIndex >= 0:
        self.cards_infos[self.currentIndex].setSelected(True, True)
  
  
  def search(self, keyWord: str):
    """ search icons """
    items = self.trie.items(keyWord.lower())
    indexes = {i[1] for i in items}
    self.flowLayout.removeAllWidgets()

    for i, card in enumerate(self.cards):
        isVisible = i in indexes
        card.setVisible(isVisible)
        if isVisible:
            self.flowLayout.addWidget(card)
            
  def showAllImages(self):
    
    #D:\Qt_project\2024\image_search\thumbnail C:/Users/hansolo/Pictures
    self.image_source_loader_thread=ImageSourceLoaderThread(r"D:\Qt_project\2024\image_search\thumbnail",recur=True)
    self.image_source_loader_thread.imageLoaded.connect(self.onImageLoaded)
    self.image_source_loader_thread.finished.connect(self.onImageLoadingFinished)
    self.image_source_loader_thread.start()
    
  
  def load_card_chunk(self):
 
    if self.loaded_cards_num>len(self.image_data):
      print("load_card_chunk already")
      return

    
    current_idx=self.loaded_chunks_size*self.max_cards_per_chunk
    next_idx=current_idx+self.max_cards_per_chunk
    for index in range(current_idx,next_idx):
      if index<len(self.image_data):
        idx,image_name,image_path=self.image_data[index]
        self.addIcon(idx,image_path,str(idx)+' '+image_name)
        self.loaded_cards_num=self.loaded_cards_num+1
        # print(f"addIcon :{idx}")
      else:
        if self.loadImageLazy:
          self.loaded_cards_num=len(self.image_data)
          # print(f"将剩余{self.loaded_cards_num}加载完")
          self.loadVisableCards(current_idx,len(self.image_data))
        break
      
      
    if next_idx<len(self.image_data):
      self.loadVisableCards(current_idx,next_idx)
      self.loaded_chunks_size=self.loaded_chunks_size+1
    # print("-------------------------------------------------------")
  
  def onImageLoaded(self,image_files:list):
    self.image_data = image_files
    
    self.load_card_chunk()

    print("预加载完成")
    self.updateContentSize()
    self.updataVisableCards()
    
    
  def onImageLoadingFinished(self):
    print("加载完成")
    self.image_source_loader_thread.deleteLater()
    self.image_source_loader_thread = None

  def createCommandBarFlyout(self,pos):
    view = CommandBarView(self)

    view.addAction(Action(FIF.SHARE, self.tr('Share')))
    view.addAction(Action(FIF.SAVE, self.tr('Save')))
    view.addAction(Action(FIF.HEART, self.tr('Add to favorate')))
    view.addAction(Action(FIF.DELETE, self.tr('Delete')))

    view.addHiddenAction(Action(FIF.PRINT, self.tr('Print'), shortcut='Ctrl+P'))
    view.addHiddenAction(Action(FIF.SETTING, self.tr('Settings'), shortcut='Ctrl+S'))
    view.resizeToSuitableWidth()
    Flyout.make(view, pos, self, FlyoutAnimationType.SLIDE_LEFT)
    
  def resizeEvent(self, event):
    print(self.scrollWidget.width(),self.scrollWidget.height())
    return super().resizeEvent(event)
   
class ImageInterface(ImageGalleryInterface):
  """ Image interface """

  def __init__(self, parent=None):
    
    t = Translator()
    super().__init__(
        title=t.images,
        subtitle="asdasdasd",
        parent=parent
    )
    self.setObjectName('imagenInterface')


    
    self.imageIconView = ImageCardView(self)
    self.vBoxLayout.addWidget(self.imageIconView)
    
    # self.toolBar.buttonLayout.removeWidget(self.toolBar.themeButton)
    # self.toolBar.themeButton=None
    # self.toolBar.vBoxLayout.removeItem(self.toolBar.buttonLayout)
   
  