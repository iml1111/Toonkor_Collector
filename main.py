import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from toonkor import Ui_MainWindow
from bs4 import BeautifulSoup as bs
import requests



class Toonkor(QMainWindow, Ui_MainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi(self)
		self.toonview_urllist = {}
		self.toonlist_urllist = {}
		self.toon_list.itemClicked.connect(self.list_to_view)
		self.show()

	#검색함수 http로 시작하면 url 검색 or 이름 검색
	@pyqtSlot()
	def search(self):
		self.search_btn.setText("검색 중...")
		element = self.search_bar.text()
		if element.startswith("http"):
			self.toon_listing(element)
		elif element == "":
			err = QMessageBox()
			err.about(self, "검색 실패", "검색 창을 입력해주세요!")
			self.search_btn.setText("검색")
			return
		else:
			url = "/bbs/search.php?sfl=wr_subject%7C%7Cwr_content&stx="
			try:
				html = requests.get(self.domain_edit.text() + url + element).text
			except:
				self.requests_error()
				return
			try:
				soup =  bs(html, "html.parser").findAll("div",{"class":"section-item-title"})
			except:
				self.scrap_error()
				return
			self.toonlist_Allremove()
			if len(soup) == 0:
				item = QListWidgetItem("'"+ element + "'" + " 검색 결과 없음.")
				self.toon_list.addItem(item)
				self.search_btn.setText("검색")
				return
			self.progressBar.setValue(0)
			index = 0
			for post in soup:
				post = post.find("a",{"id":"title"})
				title = post.get_text().strip()
				url = post.attrs['href']

				item = QListWidgetItem(title)
				self.toon_list.addItem(item)
				self.toonlist_urllist.update({title:url})
				index += 1
				self.progressBar.setValue(index * 100 / len(soup))
		self.search_btn.setText("검색")

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
			"이름은 쓸 필요 없어요. 경로만 지정하시고 바로 저장 버튼 누르세요!")
		if filename[0] == "":
			return
		path = '/'.join(filename[0].split("/")[:-1]) + '/'
		for toon in crawl_list:
			html = requests.get(toon[1]).text
			soup = bs(html,"lxml").find("div",{"id":"toon_img"})
			print(soup)
			soup = soup.findAll("img")
			print(soup)
			for img in soup:
				print(img.attrs['src'])
			return

	#리스트의 아이템을 누르면 뷰에 해당 목록을 보여줌 
	@pyqtSlot()
	def list_to_view(self):
		i = self.toon_list.currentRow()
		item = self.toon_list.item(i).text()
		if item.endswith("없음."): return
		self.toon_listing(self.domain_edit.text() + self.toonlist_urllist[item])
		
	#모두 선택 함수
	@pyqtSlot()
	def all_checking(self):
		if self.toon_view.count() == 0: return
		for index in range(self.toon_view.count()):
			if self.checkBox.isChecked():
				self.toon_view.item(index).setCheckState(Qt.Checked)
			else:
				self.toon_view.item(index).setCheckState(Qt.Unchecked)

	#해당 url로 만화 목록을 띄어줌
	def toon_listing(self, url):
		try:
			html = requests.get(url, verify = False).text
		except:
			self.requests_error()
			return
		try:
			soup = bs(html, "html.parser").find("table",{"class":"web_list"})
			toonview_list = soup.findAll("tr",{"class":"tborder"})
		except:
			self.scrap_error()
			return
		self.toonview_Allremove()
		self.progressBar.setValue(0)
		index = 0
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
					\n3.혹시 웹 브라우저로 접속은 잘 되나요?")
		self.search_btn.setText("검색")
	def scrap_error(self):
		err = QMessageBox()
		err.about(self, "웹 구조 분석 실패!", "1.URL은 정확한가요?\
			\n2.만화 리스트 페이지가 맞나요?")
		self.search_btn.setText("검색")

app = QApplication(sys.argv)
ex = Toonkor()
sys.exit(app.exec_())