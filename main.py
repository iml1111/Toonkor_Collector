import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from toonkor import Ui_MainWindow
from bs4 import BeautifulSoup as bs
import requests
from selenium import webdriver
import os
from PIL import Image
import shutil
import threading

s = threading.Semaphore(3)

class thr_search(threading.Thread):
	def __init__(self,window):
		super().__init__()
		self.window = window
		self.error = None
	def run(self):
		s.acquire()
		element = self.window.search_bar.text()
		if element.startswith("http"):
			try:
				self.window.toon_listing(element, self)
			except:
				self.error = 0
				return
		else:
			url = "/bbs/search.php?sfl=wr_subject%7C%7Cwr_content&stx="
			try:
				html = self.window.url_parser(self.window.domain_edit.text() + url + element).text
			except:
				self.error = 1
				return
			try:
				soup =  bs(html, "html.parser").findAll("div",{"class":"section-item-title"})
			except:
				self.error = 2
				return
			self.window.toonlist_Allremove()
			if len(soup) == 0:
				item = QListWidgetItem("'"+ element + "'" + " 검색 결과 없음.")
				self.window.toon_list.addItem(item)
				self.window.search_btn.setText("검색")
				return
			self.window.progressBar.setValue(0)
			index = 0
			for post in soup:
				post = post.find("a",{"id":"title"})
				title = post.get_text().strip()
				url = post.attrs['href']

				item = QListWidgetItem(title)
				self.window.toon_list.addItem(item)
				self.window.toonlist_urllist.update({title:url})
				index += 1
				self.window.progressBar.setValue(index * 100 / len(soup))
			s.release()

class thr_ltv(threading.Thread):
	def __init__(self,window):
		super().__init__()
		self.window = window
		self.error = None
	def run(self):
		s.acquire()
		i = self.window.toon_list.currentRow()
		item = self.window.toon_list.item(i).text()
		if item.endswith("없음."): return
		self.window.toon_listing(self.window.domain_edit.text() + self.window.toonlist_urllist[item],self)
		s.release()

class thr_crawl(threading.Thread):
	def __init__(self,window, crawl_list, path):
		super().__init__()
		self.window = window
		self.crawl_list = crawl_list
		self.path = path
		self.error = None
	def run(self):
		s.acquire()
		driver = self.window.get_driver()
		self.window.progressBar.setValue(10)
		self.index = 1
		for toon in self.crawl_list:
			try:
				imglist= self.window.toon_get_source(driver, toon[1], 90 / (len(self.crawl_list) * (self.index * 0.1)))
			except:
				self.error = 11
				if len(self.crawl_list) == 1:
					self.window.msg.eclose()
					self.error = 1
					driver.quit()
					s.release()
					return
				else:
					continue
			self.window.progressBar.setValue(10 + 90 / (len(self.crawl_list) * (self.index * 0.1)))
			try:
				self.window.download(self.path, imglist, 90 * (self.index / (len(self.crawl_list))))
			except:
				self.error = 22
				if len(self.crawl_list) == 1:
					self.window.msg.eclose()
					self.error = 2
					driver.quit()
					s.release()
					return
				else:
					continue
			self.window.progressBar.setValue(10 + 90 * (self.index / (len(self.crawl_list))))
			self.index += 1
		driver.quit()
		self.window.msg.eclose()
		s.release()


class Toonkor(QMainWindow, Ui_MainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi(self)
		self.toonview_urllist = {}
		self.toonlist_urllist = {}
		self.toon_list.itemClicked.connect(self.list_to_view)
		self.setWindowIcon(QIcon('lib/tkico.png'))
		self.show()
		

	#검색함수 http로 시작하면 url 검색 or 이름 검색
	@pyqtSlot()
	def search(self):
		self.search_btn.setText("검색 중...")
		element = self.search_bar.text()
		if element == "":
			err = QMessageBox()
			err.about(self, "검색 실패", "검색 창을 입력해주세요!")
			self.search_btn.setText("검색")
			return
		th = thr_search(self)
		th.start()
		th.join()
		self.search_btn.setText("검색")
		if th.error == 1:
			self.requests_error()
		elif th.error == 2:
			self.scrap_error()
		elif th.error == 0:
			self.requests_error()
	#다운로드 함수
	@pyqtSlot()
	def crawling(self):
		crawl_list = []
		for i in range(self.toon_view.count()-1, -1, -1):
			if self.toon_view.item(i).checkState() == Qt.Checked:
				crawl_list.append(
					[self.toon_view.item(i).text(),
					self.domain_edit.text() + self.toonview_urllist[self.toon_view.item(i).text()]])
		if len(crawl_list) == 0:
			err = QMessageBox()
			err.about(self, "다운로드 실패", "선택된 만화가 없어요.")
			return
		filename = QFileDialog.getSaveFileName(self,"저장할 경로를 선택하세요",\
			"이름은 지정할 필요없어요. 원하는 경로만 지정한 후, 바로 저장을 누르세요!")
		if filename[0] == "":
			return
		path = '/'.join(filename[0].split("/")[:-1]) + '/'	
		th = thr_crawl(self, crawl_list, path)
		th.start()
		self.msg = TimerMessageBox(100000)
		self.msg.exec_()
		th.join()
		if th.error == None:
			QMessageBox.about(self,"Donwload Complete!","다운로드가 완료되었습니다!")
		elif th.error == 1:
			self.requests_error()
		elif th.error == 2:
			QMessageBox.about(self,"이미지 크롤링 실패","만화 이미지를 가져오는데 실패하였습니다!")
		elif th.error == 11 or th.error == 22:
			QMessageBox.about(self,"Donwload Complete!","다운로드는 완료되었지만 , 전체 혹은 일부의 만화는 다운로드에 실패하였습니다.")
	#리스트의 아이템을 누르면 뷰에 해당 목록을 보여줌 
	@pyqtSlot()
	def list_to_view(self):
		th = thr_ltv(self)
		th.start()
		th.join()
		
	#모두 선택 함수
	@pyqtSlot()
	def all_checking(self):
		if self.toon_view.count() == 0: return
		for index in range(self.toon_view.count()):
			if self.checkBox.isChecked():
				self.toon_view.item(index).setCheckState(Qt.Checked)
			else:
				self.toon_view.item(index).setCheckState(Qt.Unchecked)

	def url_parser(self, url):
		header = {
			"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
			AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
			"Accept":"text/html,application/xhtml+xml,application/xml;\
			q=0.9,imgwebp,*/*;q=0.8",
			"Referer": self.domain_edit.text()}
		req = requests.get(url,verify = False ,headers = header)
		return req

	def toon_get_source(self,driver, url, per):
		driver.get(url)
		soup = bs(driver.page_source, "html.parser")
		self.progressBar.setValue(10 + per * 0.5)
		obj = soup.find("div",{"id":"toon_img"})
		taglist = obj.findAll("img")
		imglist = [soup.find("div",{"class":"view-wrap"}).h1.get_text().strip()]
		title_filter = '\\/<>:?!*"|'
		imglist[0] = imglist[0].translate({ ord(x): y for (x, y) in zip(title_filter, "          ") })
		for tag in taglist:
			if tag.attrs['src'].startswith("http"):
				imglist.append(tag.attrs['src'])
			else:
				imglist.append(self.domain_edit.text() + tag.attrs['src'])
		return imglist

	def get_driver(self):
		options = webdriver.ChromeOptions()
		options.add_argument('headless')
		options.add_argument('window-size=1920x1080')
		options.add_argument("disable-gpu")
		options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
		options.add_argument("lang=ko_KR")
		driver = webdriver.Chrome("./chromedriver", chrome_options=options)
		driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() {return[1, 2, 3, 4, 5];},});")
		driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return ['ko-KR', 'ko']}})")
		return driver

	def download(self, path, imglist, per):	
		try:
			os.makedirs(os.path.join(path + imglist[0]))
		except:
			pass
		path = path + imglist[0] + '/'
		index = 1
		for imgurl in imglist[1:]:
			req = self.url_parser(imgurl)
			with open(path + imglist[0] +"_"+ "%03d" % index + ".jpg", "wb") as file:
				file.write(req.content)
			self.progressBar.setValue(10 + per * (index /  len(imglist[1:])))
			index += 1
		if self.pdf_btn.isChecked():
			self.makePDF(path, imglist[0])

	def makePDF(self, path, title):
		imglist = [path + i for i in os.listdir(path) if i.endswith(".jpg")]
		pdf_name = '/'.join(path.split('/')[:-2]) + '/' + title + ".pdf"
		im1 = Image.open(imglist[0])
		im_list = []
		for i in imglist[1:]:
			im_list.append(Image.open(i))
		im1.save(pdf_name, "PDF", resolution = 100.0, save_all = True, append_images = im_list)
		shutil.rmtree(path)

	#해당 url로 만화 목록을 띄어줌
	def toon_listing(self, url,th):
		html = self.url_parser(url).text
		try:
			soup = bs(html, "html.parser").find("table",{"class":"web_list"})
			toonview_list = soup.findAll("tr",{"class":"tborder"})
		except:
			th.error = 2
			return
		self.toonview_Allremove()
		self.progressBar.setValue(0)
		index = 0
		if len(toonview_list) == 0:
			item = QListWidgetItem("만화 없음")
			self.toon_view.addItem(item)
			return
			
		for post in toonview_list:
			post = post.find("td",{"class":"content__title"})
			title = post.get_text().strip()
			url = post.attrs['data-role']

			item = QListWidgetItem(title)
			item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
			item.setCheckState(Qt.Unchecked)
			self.toon_view.addItem(item)
			self.toonview_urllist.update({title:url})
			index += 1
			self.progressBar.setValue(index * 100 / len(toonview_list))


	def toonview_Allremove(self):
		listItems =[]
		for index in range(self.toon_view.count()):
   			listItems.append(self.toon_view.item(index))
		if not listItems: return
		for item in listItems:
			self.toon_view.takeItem(self.toon_view.row(item))
		self.toonview_urllist = {}

	def toonlist_Allremove(self):
		listItems =[]
		for index in range(self.toon_list.count()):
   			listItems.append(self.toon_list.item(index))
		if not listItems: return
		for item in listItems:
			self.toon_list.takeItem(self.toon_list.row(item))
		self.toonlist_urllist = {}

	def requests_error(self):
		err = QMessageBox()
		err.about(self, "홈페이지 접근에 실패했습니다!", "1.URL은 정확한가요?\
					\n2.인터넷은 잘 되나요?\
					\n3.혹시 웹 브라우저로는 접속이 잘 되나요?")
		self.search_btn.setText("검색")
	def scrap_error(self):
		err = QMessageBox()
		err.about(self, "웹 구조 분석 실패!", "1.URL은 정확한가요?\
			\n2.만화 리스트 페이지가 맞나요?")
		self.search_btn.setText("검색")

class TimerMessageBox(QMessageBox):
    def __init__(self, timeout=3, parent=None):
        super(TimerMessageBox, self).__init__(parent)
        self.setWindowTitle("Now Downloading......")
        self.time_to_wait = timeout
        self.setText("만화가 다운로드되는 중입니다.......")
        self.setStandardButtons(QMessageBox.NoButton)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()

    def changeContent(self):
        self.setText("만화가 다운로드되는 중입니다.......")
        self.time_to_wait -= 1
        if self.time_to_wait <= 0:
            self.close()

    def eclose(self):
    	self.close()

    def closeEvent(self, event):
    	self.timer.stop()
    	event.accept()
        

app = QApplication(sys.argv)
ex = Toonkor()
sys.exit(app.exec_())