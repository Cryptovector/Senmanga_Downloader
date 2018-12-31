import shutil
import requests
import os
import argparse
import threading
from lxml import html

threadcount = 0
Maxthread = 30
lock = threading.Lock()
threadready = threading.Event()

def Wait_for_threads():
	while threadcount: #thread.join() is to slow 
		threadready.wait()
		threadready.clear()

def Download_Image(Newurl, imgpath):
	global threadready
	global threadcount 
	global lock

	lock.acquire()
	threadcount += 1
	lock.release()

	if not os.path.exists(imgpath):
		session = requests.Session()
		response = session.get(Newurl)
		if response.status_code == 200:
			tree = html.fromstring(response.content)
			Imgurl = tree.xpath('//*[@id="picture"]')[0].get('src')
			print('Download image: '+ Imgurl.split('?')[0])  #command line
			response = session.get(Imgurl, stream=True)
			file = open(imgpath, 'wb')
			print('Save image: '+imgpath)  #command line
			file.write(response.raw.data)
			file.close()
		else:
			print("Manga image url doesn't exist")
	else:
		print("Image already on Disk: "+imgpath)			

	lock.acquire()
	threadcount -= 1
	lock.release()
	threadready.set() #Ready signal

def Download_Manga_Chapter(path, url):#
	global threadready

	response = requests.get(url)
	if response.status_code == 200:
		tree = html.fromstring(response.content)
		Pagenum = int(tree.xpath('//*[@id="reader"]/div[3]/span[3]/text()')[2][4:-1])

		Newpath = path+'\\'+url.split('/')[-2]
		if not os.path.exists(Newpath):
			os.makedirs(Newpath)

		for i in range(Pagenum):
			Newurl = url[:-1]+str(i+1)
			imgpath = Newpath+'\\'+str(i+1)+'.png'	

			if threadcount == Maxthread:
				threadready.wait()

			Newthread = threading.Thread(target=Download_Image, args= (Newurl, imgpath))
			Newthread.start()
			threadready.clear()

	else:
		print("Manga url doesn't exist")


def Get_Manga_Chapter_list(url):
	Urllist = []
	Chaptercount = None
	Iter_ = 2

	response = requests.get(url)
	if response.status_code == 200:
		tree = html.fromstring(response.content)

		while True:
			try:
				Iter_  += 1
				temp_html = tree.xpath('//*[@id="content"]/div[4]/div[2]/div['+str(Iter_)+']/div[1]/a')
				Urllist.append(temp_html[0].get('href'))
				print("Chapter url: "+ Urllist[-1]) #command line
			except:
				break	

		return Urllist		
	
	else:
		print("Manga url doesn't exist")


def Download_all_Manga_Chapter(path , url):
	Urllist = reversed(Get_Manga_Chapter_list(url))

	for Urlentry in Urllist:
		print(Urlentry)
		Download_Manga_Chapter(path, (Urlentry))		

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Senmanga Downloader')
	parser.add_argument('-c','--Chapter', action='store_false')
	parser.add_argument('-m','--Manga', action='store_false')
	parser.add_argument('-u', '--Url',
		action="store", dest="Url",
		help="Url for Chapter or Manga", default="")
	parser.add_argument('-d', '--destination',
		action="store", dest="destination",
		help="Path for Manga files", default="")	
	
	args = parser.parse_args()

	if (args.Chapter ^ args.Manga):

		if not args.Chapter:
			Download_all_Manga_Chapter(args.destination, args.Url)
			Wait_for_threads()
		if not args.Manga:
			Download_Manga_Chapter(args.destination, args.Url)
			Wait_for_threads()

	else:
		print("Usage: use -c or -m")