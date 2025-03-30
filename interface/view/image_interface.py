# coding:utf-8
from PyQt5.QtCore import Qt, QPoint,QThread,pyqtSignal,pyqtSlot,QTimer,QEvent,QUrl
from PyQt5.QtGui import QPixmap, QDesktopServices,QFontMetrics
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget, QHBoxLayout


from qfluentwidgets import SmoothScrollArea, FlowLayout, ToggleToolButton,BodyLabel, SingleDirectionScrollArea,ImageLabel,SearchLineEdit,CommandBarView,Action,Flyout,FlyoutAnimationType,PushButton,StrongBodyLabel,IconWidget,LineEditButton,LineEdit

from qfluentwidgets import FluentIcon as FIF

from .image_gallery_interface import ImageGalleryInterface
from ..common.style_sheet import StyleSheet
from ..common.config import cfg
from ..common.translator import Translator

from pathlib import Path
import os

from .image_interface_utils import CustomSearchLineEdit,TagButton,ExampleCard

from data_services.config import app_config

from ..common.service_conntion import ServiceConnection,ImageInfo

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
  
  
  def search_image(self,folder_path,recur=False)-> list[ImageInfo]:
    image_files: list[ImageInfo] = []
    idx=0
    if recur:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                  file_path=Path(os.path.join(root, file)).as_posix()
                  image_files.append(ImageInfo(idx,file , file_path))
                  idx=idx+1
                # image_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
              file_path=Path(os.path.join(folder_path, file)).as_posix()
              image_files.append(ImageInfo(idx,file , file_path))
              idx=idx+1
              
    return image_files




class ImageCard(QFrame):
  imageCardClicked=pyqtSignal(QPoint)
  def __init__(self, path,filename,parent = None):
    super().__init__(parent=parent)
    
    self.maxTextWidth=110 #180 180
    self.maxCardWidth=150 #220 150
    
    self.setFixedSize(self.maxCardWidth, self.maxCardWidth)
    self.image_path=path
    self.image_name=filename
    self.imageWidget = QWidget(self)
    # self.image_label=ImageLabel(self)
    self.imageLabel=ImageLabel(self)
    self.imageNameLable=QLabel(self)
    self.isImageLoaded = False  # 标记图片是否加载
    
    self.image_info:ImageInfo
    
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
    
    print(self.image_info.image_path)
    print(self.image_info.description)
    self.computClickedPos()
    
    
  def set_image(self,index,image_info):
    if self.isImageLoaded:
      return 
    
    print(f"加载 图片 {index}")

    self.image_info=image_info
    
    try:
      os.path.exists(self.image_path)
    except OSError:
      print(f"图片路径错误：{self.image_path}")
    else:
      pixmap=QPixmap(self.image_path)
      if not pixmap.isNull():
      # pixmap=QPixmap(self.image_path)
        pixmap=pixmap.scaled(self.maxTextWidth, self.maxTextWidth,Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(pixmap)
        self.isImageLoaded=True
        
        # print(f"加载图片 {index}")
        # self.imageWidgetLayOut.setAlignment(Qt.AlignHCenter)
        self.imageWidgetLayOut.update()
        self.update()
      else:
        print(f"无法加载图片：{self.image_path}")
    
      


  def computClickedPos(self):

    x = self.imageLabel.width()
    pos = self.imageLabel.mapToGlobal(QPoint(x, 0))
    print(pos.x(),pos.y())
    self.imageCardClicked.emit(pos)
    # Flyout.make(view, pos, self, FlyoutAnimationType.FADE_IN)
    
class ImageCardView(QWidget):
  
  def __init__(self, parent=None):
    
    super().__init__(parent)
    
    self.searchLineEdit = CustomSearchLineEdit(self)
    
    self.searchSettingButton = ToggleToolButton(FIF.FILTER, self)
    
    self.imageLimitLineEdit=LineEdit()
    self.imageLimitLabel=BodyLabel("图片数量限制<=")
    self.imageScoreLimitLineEdit=LineEdit()
    self.imageScoreLimitLabel=BodyLabel("Score>=")
    self.searchComboLayout=QHBoxLayout()
    self.imageSearchSettingHide=True
    
    self.view = QFrame(self)
    self.scrollArea = SmoothScrollArea(self.view)
    self.scrollWidget = QWidget(self.scrollArea)
    
    self.vBoxLayout = QVBoxLayout(self)
    self.hBoxLayout = QHBoxLayout(self.view)
    self.flowLayout = FlowLayout(self.scrollWidget, isTight=True)
    
    self.image_data : list[ImageInfo]=[]  # 存储所有图片路径和文件名 = [] 
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
    # self.vBoxLayout.addWidget(self.searchLineEdit)
    
    self.searchSettingButton.setObjectName("searchSettingButton")
    self.searchComboLayout.addWidget(self.searchLineEdit)
    self.searchComboLayout.addWidget(self.searchSettingButton)
    
    
    self.searchSettingButton.clicked.connect(self.showSearchSetting)
    
    # self.searchComboLayout.addWidget(self.imageLimitLabel)
    # self.searchComboLayout.addWidget(self.imageLimitLineEdit)
    # self.searchComboLayout.addWidget(self.imageScoreLimitLabel)
    # self.searchComboLayout.addWidget(self.imageScoreLimitLineEdit)
    
    
    
    self.searchComboLayout.addStretch()
    
    
    self.vBoxLayout.addLayout(self.searchComboLayout)
    self.addSearchSettingLayout()
    
    self.tagCardWidget,self.tagCardLayout=self.createWidget()
    self.tagCard = ExampleCard(self.tr('标签'), self.tagCardWidget, stretch=1)
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
  
  
  def addSearchSettingLayout(self):
    self.imageLimitLineEdit.setText(str(200))
    self.imageScoreLimitLineEdit.setText(str(0.45))
    
    self.imageLimitLabel.setFixedWidth(100)
    self.imageLimitLineEdit.setFixedWidth(50)
    self.imageScoreLimitLabel.setFixedWidth(52)
    self.imageScoreLimitLineEdit.setFixedWidth(52)
    
    self.searchSettingLayout=QHBoxLayout()
    self.searchSettingLayout.addWidget(self.imageLimitLabel)
    self.searchSettingLayout.addWidget(self.imageLimitLineEdit)
    self.searchSettingLayout.addWidget(self.imageScoreLimitLabel)
    self.searchSettingLayout.addWidget(self.imageScoreLimitLineEdit)
    self.searchSettingLayout.addStretch()
    self.vBoxLayout.addLayout(self.searchSettingLayout)
    
    for i in range(self.searchSettingLayout.count()):
      item=self.searchSettingLayout.itemAt(i)
      if item.widget():
        item.widget().hide()
  
  def showSearchSetting(self):
    
    if self.imageSearchSettingHide is True:
      self.imageSearchSettingHide=False
      for i in range(self.searchSettingLayout.count()):
        item=self.searchSettingLayout.itemAt(i)
        if item.widget():
          item.widget().show()
    else:
      self.imageSearchSettingHide=True
      for i in range(self.searchSettingLayout.count()):
        item=self.searchSettingLayout.itemAt(i)
        if item.widget():
          item.widget().hide()
        
  def createWidget(self, animation=False):
    # texts = [
    #     self.tr('Star Platinum'), self.tr('Hierophant Green'),
    #     self.tr('Silver Chariot'), self.tr('Crazy diamond'),
    #     self.tr("Heaven's Door"), self.tr('Killer Queen'),
    #     self.tr("Gold Experience"), self.tr('Sticky Fingers'),
    #     self.tr("Sex Pistols"), self.tr('Dirty Deeds Done Dirt Cheap'),
    # ]

    widget = QWidget()
    layout = FlowLayout(widget, animation)

    layout.setContentsMargins(0, 0, 0, 0)
    layout.setVerticalSpacing(10)
    layout.setHorizontalSpacing(10)

    # for text in texts:
    #   tagbutton=TagButton(text)
    #   tagbutton.button_delete.connect(self.delete_TagButton)
    #   self.tagButtons.append(tagbutton)
    #   layout.addWidget(tagbutton)
    return widget,layout
  
  @pyqtSlot(TagButton)
  def delete_TagButton(self):
    print(self.sender().text())
    for button in self.tagButtons:
      if button.text()==self.sender().text():
        self.tagCardLayout.removeWidget(button)
        self.tagButtons.remove(button)
        button.deleteLater()
        button=None
        print("删除按钮")
        self.tagCardLayout.update()
        break

  def add_TagButton(self,text):
    tagbutton=TagButton(text)
    tagbutton.button_delete.connect(self.delete_TagButton)
    self.tagButtons.append(tagbutton)
    self.tagCardLayout.addWidget(tagbutton)
    pass
    
  def loadImage(self):
    """从队列中加载图片"""
    if len(self.imageQueue)==0:
        return
    idx = self.imageQueue.pop(0)  # 从队列头部取卡片
    self.allCards[idx].set_image(idx,self.image_data[idx])
    print(f"{idx}/ {len(self.image_data)}")
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
          print(f"{self.lazyIndex} /{len(self.image_data)}")
          card.set_image(self.lazyIndex,self.image_data[self.lazyIndex])
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
    print(f"加载图片 {start_idx}~{end_idx}")
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
  
  
  @pyqtSlot()
  def __setQss(self):
    self.view.setObjectName('imageView')
    self.scrollWidget.setObjectName('scrollWidget')
    self.scrollArea.setObjectName("scrollArea")
    
    
    StyleSheet.IMAGE_INTERFACE.apply(self)
    StyleSheet.IMAGE_INTERFACE.apply(self.scrollWidget)
    StyleSheet.IMAGE_INTERFACE.apply(self.scrollArea)
     
    if self.currentIndex >= 0:
        self.cards_infos[self.currentIndex].setSelected(True, True)
  
  @pyqtSlot(str)
  def search(self, keyWord: str):
    """ search image """
    print(keyWord)
    self.add_TagButton(keyWord)
    
    self.serice_connect_thread=ServiceConnection(key_words=keyWord,limit=int(self.imageLimitLineEdit.text()))
    
    self.serice_connect_thread.images_info.connect(self.display_searched_images)
    self.serice_connect_thread.finished.connect(self.on_serice_connect_thread_finished)
    self.serice_connect_thread.start()
    # items = self.trie.items(keyWord.lower())
    # indexes = {i[1] for i in items}
    # self.flowLayout.removeAllWidgets()

    # for i, card in enumerate(self.cards):
    #     isVisible = i in indexes
    #     card.setVisible(isVisible)
    #     if isVisible:
    #         self.flowLayout.addWidget(card)
  
  @pyqtSlot(list)
  def display_searched_images(self,images_info: list[ImageInfo]):
    self.resetData()
 

    self.image_data = images_info
    self.load_card_chunk()
    print("预加载完成")
    self.updateContentSize()
    self.updataVisableCards()
  
  def on_serice_connect_thread_finished(self):
    self.serice_connect_thread.deleteLater()
    self.serice_connect_thread=None
  
  def resetData(self):
    self.flowLayout.removeAllWidgets()
    self.loaded_chunks_size=0
    self.loaded_cards_num=0
    self.loadImageLazy=True #是否懒加载
     # 添加懒加载相关
    self.imageQueue = []  # 待加载图片队列
    self.lazyIndex = 0  # 用于延迟加载的索引
    self.cards_per_row = 0  # 每行卡片数
    self.image_data = []  # 存储所有图片路径和文件名 = [] 
    self.currentIndex = -1
    for idx in range(0,len(self.allCards)):
      self.allCards[idx].imageLabel.deleteLater()
      self.allCards[idx].deleteLater()
      self.allCards[idx]=None
    self.allCards: list[ImageCard] = []
    self.cards_infos = []
    
    self.scrollArea.verticalScrollBar().setValue(0)
    self.flowLayout.update()
  @pyqtSlot()  
  def showAllImages(self):
    
    self.resetData()
    

    self.image_source_loader_thread=ImageSourceLoaderThread(app_config.thumbnail_folder,recur=True)
    self.image_source_loader_thread.imageLoaded.connect(self.onImageLoaded)
    self.image_source_loader_thread.finished.connect(self.onImageLoadingFinished)
    self.image_source_loader_thread.start()
    
  
  def load_card_chunk(self):
    print(self.loaded_cards_num)
    if self.loaded_cards_num>len(self.image_data):
      print("load_card_chunk already")
      return

    
    current_idx=self.loaded_chunks_size*self.max_cards_per_chunk
    next_idx=current_idx+self.max_cards_per_chunk
    
    # is_remain_card=False
    for index in range(current_idx,next_idx):
      if index<len(self.image_data):
     
        idx=self.image_data[index].idx
        image_name=self.image_data[index].image_name
        image_path=self.image_data[index].image_path
        self.addIcon(idx,image_path,str(idx)+' '+image_name)
        self.loaded_cards_num=self.loaded_cards_num+1
        print(f"addIcon :{idx}")
      else:
        if self.loadImageLazy:
          # is_remain_card=True
          self.loaded_cards_num=len(self.image_data)
          print(f"将剩余{current_idx}-{self.loaded_cards_num}加载完")
          self.loadVisableCards(current_idx,len(self.image_data))
        break
      
      
    print(f"next_index {next_idx} / {len(self.image_data)}")
      
    if next_idx<=len(self.image_data):
      self.loadVisableCards(current_idx,next_idx)
      self.loaded_chunks_size=self.loaded_chunks_size+1
    # print("-------------------------------------------------------")
  
  @pyqtSlot(list)
  def onImageLoaded(self,image_files:list[ImageInfo]):
    self.image_data = image_files
    
    self.load_card_chunk()

    print("预加载完成")
    self.updateContentSize()
    self.updataVisableCards()
    
  @pyqtSlot()
  def onImageLoadingFinished(self):
    print("加载完成")
    self.image_source_loader_thread.deleteLater()
    self.image_source_loader_thread = None
    
  @pyqtSlot(QPoint)
  def createCommandBarFlyout(self,pos:QPoint):
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
   
  