from PyQt5.QtCore import QThread
import requests
import sys



class ServiceConnection(QThread):
  def __init__(self, parent = None):
    super().__init__(parent)
    
    
  def run(self):
    pass