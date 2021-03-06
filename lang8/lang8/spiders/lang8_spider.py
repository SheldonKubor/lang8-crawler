import scrapy
import re
from scrapy import Selector
from scrapy.http import FormRequest
from scrapy.http import HtmlResponse
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.selector import HtmlXPathSelector
from lang8.items import Lang8Item, CorrectionItem

class Lang8Spider(CrawlSpider):
	name 		= "lang8"
	allowed_domains	= ["lang-8.com"]
	scrapying_url = "http://lang-8.com/88284/journals"
	rules = (
			Rule(LinkExtractor(allow=("\d+/journals/\d+",)), callback='parse_item'),
	)
	def start_requests(self):
		yield scrapy.Request('https://lang-8.com/login', callback=self.login)

	def login(self, response):
		formdata = {'username':'anta.huang@gmail.com','password':'ck103kw'}
		yield FormRequest.from_response(response,
										formnumber=1,
										formdata=formdata,
										clickdata={'name':'commit'},
										callback=self.logged_in)

	def logged_in(self, response):
		#yield scrapy.Request("http://lang-8.com/88284/journals")
		for i in range(1, 10000, 1):
			scrapying_url = "http://lang-8.com/" + str(i) + "/journals"
			yield scrapy.Request(scrapying_url)

	def parse_item(self, response):
		self.log('parsing %s' % response.url)
		item = Lang8Item()
		hxs = Selector(response)
		correction_list = hxs.xpath('//div[@class="correction_box"]')
		to_be_compile = [r"<span class=\"f_red\">(.*?)</span>",
						 r"<span class=\"sline\">(.*?)</span>",
						 r"<span class=\"f_gray\">(.*?)</span>"
						]
		COMPILED_RE=[]
		for one in to_be_compile:
			COMPILED_RE.append(re.compile(one))
		TAG_RE = re.compile(r"<.*?>")

		item['correction']=[]
		item['url']=response.url
		if correction_list:
			for co in correction_list:
				correct_xpath = co.xpath('.//li[@class="corrected correct"]')
				if not correct_xpath:
					continue
				incorrect = co.xpath('.//li[@class="incorrect"]/text()').extract()[0].encode("utf-8")
				correct = correct_xpath.xpath('.//p[1]').extract()[0].encode("utf-8")
#				self.log("type of correct=%s" % type(correct))
				for one in COMPILED_RE:
					correct = re.sub(one, "", correct)
				correct = re.sub(TAG_RE, "", correct)
				#self.log("correct=%s incorrect=%s" % (correct, incorrect))
				co_item = CorrectionItem()
				co_item['correct'] = correct
				co_item['incorrect'] = incorrect
				item['correction'].append(dict(co_item))
		main_list = hxs.xpath('//div[@id="body_show_ori"]').extract()
		if main_list:
			main = main_list[0]
			main = re.sub(TAG_RE, "", main)
			item['main'] = main
			#self.log("main=%s" % main)
		return item

