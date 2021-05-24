# py-crawler

Простой скрипт на Python для создания карты сайта. Многопоточная обработка ссылок с использованием модуля Threading.
Возможность работы на версиях Python отличных от 3.9 не проверялась.

## Установка

```
$ git clone https://github.com/Olegcey/py-crawler
$ pip install -r py-crawler/requirements.txt
```

## Использование

```
$ py-crawler.py --help
usage: py-crawler.py [-h] [-w w] [-t T] [-m M] url outfile

Python crawler, example: py-crawler.py https://example.com/ out.xml -w 50 -t 3 -m 1000000

positional arguments:
  url                URL for crawling
  outfile            path to output XML file

optional arguments:
  -h, --help         show this help message and exit
  -w w, --workers w  count of threads to use
  -t T, --timeout T  page load timeout
  -m M, --max M      maximum count of pages to crawl
```
