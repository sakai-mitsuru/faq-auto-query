# -*- coding: utf-8 -*-

import os
import sys
import json
import wave
import itertools
import contextlib
#import urllib2
import six

import mimetypes
import types

import codecs
import csv
import re

#from types import *

from six.moves import urllib

proxies = {"https": "http://proxy.toshiba-sol.co.jp:8080/"}
handler = urllib.request.ProxyHandler(proxies)
opener = urllib.request.build_opener(handler)



####利用者依存のパラメータ####
class BaseInfo:

	#RECAIUSサービス利用アカウント及びパスワード
	service_id = "iistry-1009" #[ERP]環境環境向け
	password   = "!Iis-ySRvKFk3" #[ERP]開発環境向け

	#認証システムのトークンの有効期限
	expiry_sec = 3600  # 1時間


	#ユーザ識別名(例)
	uuName = "ErpUser003"

	#知識ベース名称(例) (知識ベース作成時に利用)
	dbname = "ContactFaq_sample"

	#知識ベースID(例)　　知識ベースを作成すると自動的にidが割り振られるので、それを以下に記入する。
	dbid = "1312"


####利用者依存のパラメータ END####

class MyWebHandler:
	def __init__(self, url, data=None, headers=None, method=None):
		if six.PY2:
			self.req = urllib.request.Request(url, data, headers)
			if method is not None:
				self.req.get_method = lambda: method
		else:
			self.req = urllib.request.Request(url, data, headers, method=method)

		self.response = opener.open(self.req)

	def read(self):
		the_page = self.response.read()
#		print(the_page)
#		if isinstance(the_page, six.binary_type):
#			the_page = the_page.decode("UTF-8")
		return the_page

	def readlines(self):
		the_pageline = self.response.readlines()
		#if isinstance(the_pageline, six.binary_type):
		#	the_pageline = the_pageline.decode("UTF-8")
		#print(the_pageline)
		return the_pageline

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, tb):
		self.response.close()
		if isinstance(exc_value, urllib.error.HTTPError):
			six.print_("HTTP Error {0}".format(exc_value.code), file=sys.stderr)
			the_page = exc_value.read()
			six.print_(the_page, file=sys.stderr)

class RecaiusAuth:
	# baseurl = "https://try-api.recaius.jp/auth/v2"
	baseurl = "https://api.recaius.jp/auth/v2"
	def __init__(self, service_id, password):
		url = RecaiusAuth.baseurl + "/tokens"

		# サービスごとのアカウントをここで与える
		user = {"service_id": service_id, "password": password}

		# 知識探索用
		#values = {"knowledge_explorer": user}

		values = {
			"knowledge_explorer": user,
			"expiry_sec": BaseInfo.expiry_sec
		}

		headers = {"Content-Type" : "application/json"}
		data = six.b(json.dumps(values))

		with MyWebHandler(url, data, headers) as handler:
			the_page = handler.read()
		result = json.loads(the_page.strip())
		self.token = result["token"]

		#テスト挿入
		# six.print_("self.token =" + self.token)

		#six.print_("Expiry sec:", result["expiry_sec"], file=sys.stderr)
		self.is_closed = False

	def close(self):
		if not self.is_closed:
			url = RecaiusAuth.baseurl + "/tokens"
			data = six.b("")
			headers = {"X-Token" : self.token}
			with MyWebHandler(url, data, headers, "DELETE") as handler:
				the_page = handler.read()
			self.is_closed = True
			#six.print_(>>sys.stderr, "Logout succeeded", file=sys.stderr)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

class KnowledgeDB:
	# baseurl = "https://try-api.recaius.jp/asr/v2"
	baseurl = "https://api.recaius.jp/iip/v2"

	@staticmethod
	def multipart_formdata(form_dict, boundary):
		disposition = 'Content-Disposition: form-data; name="{0}"'
		lines = []
		for k, v in six.iteritems(form_dict):
			lines.append(six.b("--" + boundary))
			lines.append(six.b(disposition.format(k)))
			lines.append(six.b(""))
			lines.append(v)
		lines.append(six.b("--" + boundary + "--"))
		lines.append(six.b(""))
		value = six.b("\r\n").join(lines)
		return value

	@staticmethod
	def multipart_formdataEx(form_dict, boundary):
		disposition = 'Content-Disposition: form-data; name="{0}"'
		lines = []
		for k, v in six.iteritems(form_dict):
			lines.append(six.b("--" + boundary))

			if k == "file":
				six.print_("START file")
				#lines.append(six.b(disposition.format(k)) + six.b('; filename="ITLaw.txt"'))
				lines.append(six.b(disposition.format(k)) + six.b('; filename=' +  BaseInfo.upfileName))

				#lines.append(six.b('Content-Type: %s' % mimetypes.guess_type('ITLaw.txt')[0]))
				lines.append(six.b('Content-Type: %s' % mimetypes.guess_type(BaseInfo.upfileName)[0]))

			else:
				six.print_("START notfile")
				lines.append(six.b(disposition.format(k)))

			lines.append(six.b(""))
			lines.append(v)

		lines.append(six.b("--" + boundary + "--"))
		lines.append(six.b(""))

		value = six.b("\r\n").join(lines)
		return value

	def __init__(self, auth, uuName):
		self.auth_token = auth.token
		# six.print_("KnowledgeDB self.auth_token =" + self.auth_token)
		self._uuName = uuName
		self.is_closed = False
		self.dbid = BaseInfo.dbid

	def close(self):
		if not self.is_closed:
			self.is_closed = True

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()


	#入力テキストキーワード(特徴づける語)取得
	def getKeywords(self,uuName,data):
		# six.print_("入力テキストキーワード START")

		values = {
			"text":six.b("It happens to be an could")
		}

		#500文字以内テキスト
		#urlp = BaseInfo.textDocShort
		urlp = data

		# p = "text=" + urllib.parse.quote_plus(urlp ,encoding="utf-8")
		p = "text=" + urlp

		url =  KnowledgeDB.baseurl + "/texts/keywords?" + p
		# six.print_("url getMorph =" + url)
		boundary = "--------Boundary"
		headers = {
			"Content-Type": "multipart/form-data; boundary={0}".format(boundary),
			"X-Token": self.auth_token,
			"X-User":self._uuName
			}

		data = KnowledgeDB.multipart_formdata(values, boundary)
		# six.print_("START getMorph with MyWebHandler")

		data=None
		with MyWebHandler(url, data, headers, "GET") as handler:
			# six.print_("START handler.read")
			the_page = handler.read()
			# six.print_("END SearchWord")
			# six.print_("実行結果")
			# six.print_(the_page)
			_the_page = json.loads(the_page)
			return _the_page[u'keywords']

def main():

	service_id = BaseInfo.service_id
	password = BaseInfo.password

	# six.print_("DO START")

	finalKeywordList = []

	with RecaiusAuth(service_id, password) as auth:

		with KnowledgeDB(auth, BaseInfo.uuName) as kdb:

			# tag_str_t = "エクセルについて教えて"
			tag_str_t = sys.argv[1].decode('shift_jis').encode('utf-8')
			tag_str_t = re.sub(r"<[^>]*?>","",tag_str_t)
			tag_str_t = re.sub("\n","",tag_str_t)
			tag_str_t = re.sub(r"\\\?","",tag_str_t) #\?の変換
			tag_str_t = re.sub(r"\?","",tag_str_t) #\?の変換
			#空白 #ダブルコーデーション空白にした
			tag_str_t = re.sub(r"[(){}\[\]\"]","　",tag_str_t)
			tag_str_t = re.sub(r"&#[a-xA-Z0-9]+;","　",tag_str_t)
			tag_str_t = re.sub(" ","　",tag_str_t)
			#エスケープ処理 クエリに対してのみの処理
			tag_str_t = re.sub(r"\\",r"\\\\",tag_str_t)
			tag_str_t = re.sub(r"\/",r"\\/",tag_str_t) #　スラッシュ

			result = kdb.getKeywords(BaseInfo.uuName,tag_str_t)
			#print result[0],result[1],result[2]
			if(len(result)==1):
				finalKeywordList.append(result[0][u'word'].encode('utf-8'))
			elif(len(result)==2):
				finalKeywordList.append(result[0][u'word'].encode('utf-8'))
				finalKeywordList.append(result[1][u'word'].encode('utf-8'))
			elif(len(result)>=3):
				finalKeywordList.append(result[0][u'word'].encode('utf-8'))
				finalKeywordList.append(result[1][u'word'].encode('utf-8'))
				finalKeywordList.append(result[2][u'word'].encode('utf-8'))

			six.print_(json.dumps(finalKeywordList,ensure_ascii=False))

if __name__ == "__main__":
	main()
