import threading
import queue
from urllib.parse import urlsplit
from xml.dom import minidom
import requests
import bs4
import robots # в urllib.robotparser есть баги
# с ними не выйдет, например, распарсить google.com/robots.txt
import xml.etree.cElementTree as Tree

import time
import argparse



class Page():
	def __init__(self, text, base, scheme):
		self.base = base
		self.scheme = scheme
		self.soup = bs4.BeautifulSoup(text, 'html.parser')
		self.links = self.findLinks()

	def findLinks(self):
		res = set()
		for i in self.soup.select('a'):
			href = i.get('href')
			if href:
				if href.startswith('//'):
					href = self.scheme + '://' + href[2:]
				res.add(href if urlsplit(href)[1] else self.base+href)
		return res

class Crawler():
	def __init__(self, url, workers=10, timeout=5, m=0, outfile='out.xml'):
		splitted = urlsplit(url)
		self.scheme = splitted.scheme
		self.rootUrl = splitted.netloc
		self.base = f'{splitted[0]}://{splitted[1]}'
		self.rfp = robots.RobotsParser.from_uri(f'{self.base}/robots.txt')
		self.session = requests.Session()
		self.workers = workers
		self.timeout = timeout
		self.max = m
		self.outfile = outfile
		self.q = queue.Queue()
		self.uniqueLinks = set()
		self.linksLock = threading.Lock()
		self.hashset = set()

		self.count = 0
		self.addLink(url)

	def addLink(self, *links):
		self.linksLock.acquire() # не изменяем множество одновременно с другим потоком
		for link in set(links) - self.uniqueLinks: # каждая необработанная ссылка
			if urlsplit(link).netloc == self.rootUrl:
				self.uniqueLinks.add(link)
				self.q.put(link)
		self.count = len(self.uniqueLinks)
		print(self.count)
		self.linksLock.release() # запись в множество занимает относительно мало времени
		# можно принебречь

	def crawlUrl(self, url):
		if self.rfp.can_fetch('*', url):
			try:
				text = self.session.get(url, timeout=self.timeout).text
				links = Page(text, self.base, self.scheme).links
				self.addLink(*links)
			except:
				pass

	def writeXML(self):
		urlset = Tree.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
		for link in self.uniqueLinks:
			url = Tree.SubElement(urlset, 'url')
			Tree.SubElement(url, 'loc').text = link

		pretty = minidom.parseString(Tree.tostring(urlset)).toprettyxml(encoding='UTF-8')
		with open(self.outfile, 'wb') as f:
			f.write(pretty)


	def worker(self):
		while self.max==0 or self.count < self.max:
			url = self.q.get()
			self.crawlUrl(url)
			self.q.task_done()
		while not self.q.empty():
			self.q.get()
			# здесь можно сохранить очередь для продолжения поиска
			self.q.task_done()

	def run(self):
		workers = [threading.Thread(target=self.worker, daemon=True) for i in range(self.workers)]
		for i in workers:
			i.start()
		self.q.join() # ждём пока все ссылки не обработаются
		self.writeXML()


def main():
	ap = argparse.ArgumentParser(description='''Python crawler,
		example: %(prog)s https://example.com/ out.xml -w 50 -t 3 -m 1000000''')
	ap.add_argument('url', type=str, help='URL for crawling')
	ap.add_argument('outfile', type=str, help='path to output XML file')
	ap.add_argument('-w', '--workers', metavar='w', type=int, default=10, help='count of threads to use')
	ap.add_argument('-t', '--timeout', metavar='T', type=int, default=5, help='page load timeout')
	ap.add_argument('-m', '--max', metavar='M', type=int, default=0, help='maximum count of pages to crawl')
	args = ap.parse_args()

	url = args.url
	if urlsplit(url).scheme == '':
		url = 'http://'+url
	print('Парсинг', url)
	c = Crawler(url, args.workers, args.timeout, args.max, args.outfile)
	s = time.time()
	c.run()
	print('Затрачено времени:', time.time()-s)
	print('Найдено ссылок:', len(c.uniqueLinks))

if __name__ == '__main__':
	main()
