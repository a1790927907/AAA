import scrapy
from snyg.settings import config
import sp_queue
from urllib.parse import quote
import re
import json
from snyg.items import SnygItem
import copy
import execjs
import numpy as np
from datetime import datetime
class SnygspSpider(scrapy.Spider):
    queue_action = sp_queue.QueueAction(**config)
    key_word = queue_action.get_and_pop_one_keyword()
    name = 'snygsp'
    allowed_domains = ['suning.com']
    start_urls = [f'https://search.suning.com/{quote(key_word.decode())}/']

    def parse(self, response):
        all_params = re.findall(r'var param = (\{.*?\});',response.text,re.S)[0].replace('\n','').replace("'",'"')
        all_data = json.loads(all_params)
        lesHoldURL = all_data['lesHoldURL'].replace('search.do?','')
        page_nums = all_data['pageNumbers']
        st = all_data['st']
        sesab = all_data['sesab']
        preciseFound = all_data['preciseFound']
        #adNumber需要设置为0,页面显示的内容为30-adNumber条，设置为0则全部显示
        base_url = 'https://search.suning.com/emall/searchV1Product.do?' + lesHoldURL + '&il=0&pg=01&iy=0&adNumber=0&isNoResult=0&n=1&id=IDENTIFYING&sub=1&st=' + st + '&jzq=' + preciseFound + '&sesab=' + sesab

        yield scrapy.Request(base_url+f'&cp=0',callback=self.parse_page_info,meta={'page_nums':page_nums,'base_url':base_url,'cp':0,'jzq':preciseFound,'paging':0},dont_filter=True)

        yield scrapy.Request(base_url + f'&cp=0', callback=self.parse_goods_detail)

    def parse_page_info(self,response):
        page_nums = response.meta['page_nums']
        base_url = response.meta['base_url']
        cp = response.meta['cp']
        paging = response.meta['paging']
        if (cp+1) <= int(page_nums):
            if paging == 0:
                new_jzq = 'jzq=' + re.findall(r'param.preciseFound="(.*?)"', response.text)[0] + '&'
                b_url = re.sub(r'jzq=.*?&', new_jzq, base_url) + '&paging=' + str(paging+1) + '&cp=' + str(cp)
                yield scrapy.Request(b_url,callback=self.parse_goods_detail)
                yield scrapy.Request(b_url,callback=self.parse_page_info,meta={'page_nums':page_nums,'base_url':base_url,'cp':cp,'jzq':new_jzq,'paging':1},dont_filter=True)
            elif paging == 1:
                new_jzq = 'jzq=' + re.findall(r'param.preciseFound="(.*?)"', response.text)[0] + '&'
                b_url = re.sub(r'jzq=.*?&', new_jzq, base_url) + '&paging=' + str(paging+1) + '&cp=' + str(cp)
                yield scrapy.Request(b_url, callback=self.parse_goods_detail)
                yield scrapy.Request(b_url, callback=self.parse_page_info,meta={'page_nums': page_nums, 'base_url': base_url, 'cp': cp, 'jzq': new_jzq,'paging': 2},dont_filter=True)
            elif paging == 2:
                new_jzq = 'jzq=' + re.findall(r'param.preciseFound="(.*?)"', response.text)[0] + '&'
                b_url = re.sub(r'jzq=.*?&', new_jzq, base_url) + '&paging=' + str(paging+1) + '&cp=' + str(cp)
                yield scrapy.Request(b_url, callback=self.parse_goods_detail)
                yield scrapy.Request(b_url, callback=self.parse_page_info,meta={'page_nums': page_nums, 'base_url': base_url, 'cp': (cp+1), 'jzq': new_jzq,'paging': 3},dont_filter=True)
            elif paging == 3:
                new_jzq = 'jzq=' + re.findall(r'param.preciseFound="(.*?)"', response.text)[0] + '&'
                b_url = re.sub(r'jzq=.*?&', new_jzq, base_url) + '&cp=' + str(cp)
                yield scrapy.Request(b_url, callback=self.parse_goods_detail)
                yield scrapy.Request(b_url, callback=self.parse_page_info,meta={'page_nums': page_nums, 'base_url': base_url, 'cp': cp, 'jzq': new_jzq,'paging': 0}, dont_filter=True)


    def parse_goods_detail(self,response):
        all_goods_info = response.xpath('//li[@doctype="1"]')
        for goods_info in all_goods_info:
            item = SnygItem()
            item['key_word'] = self.key_word.decode()
            all_title = goods_info.xpath('.//div[@class="res-info"]/div[@class="title-selling-point"]/a//text()').extract()
            no_use_title = goods_info.xpath('.//div[@class="res-info"]/div[@class="title-selling-point"]/a/@title').extract_first()
            item['title'] = ''.join([re.sub(r'\n|\r|\t| ','',i) for i in all_title if re.sub(r'\n|\r|\t| ','',i)]).replace(no_use_title,'')
            item['goods_url'] = 'https:' + goods_info.xpath('.//div[@class="res-info"]/div[@class="title-selling-point"]/a/@href').extract_first()
            item['goods_img'] = 'https:' + goods_info.xpath('.//div[@class="res-img"]/div[@class="img-block"]//img/@src').extract_first()
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(item['goods_url'],callback=self.parse_all_goods_info,meta={'item':item_copy})


    def parse_all_goods_info(self,response):
        item = response.meta['item']
        sn_passpartnum = re.findall(r'passPartNumber":"(.*?)"',response.text)[0]
        sn_partNumber_list = re.findall(r'partNumber":"(.*?)"',response.text)
        cat_id = re.findall(r'(.*?)\.html',response.url.split('/')[-1])[0]
        for p in sn_partNumber_list:
            if cat_id in p:
                sn_partNumber = p
                break
        else:
            print('-'*100)
            return
        vendor_code = re.findall(r'"vendorCode":"(.*?)"',response.text)[0]
        procatecode = response.xpath('//input[@name="procateCode"]/@value').extract_first()
        try:
            volume = re.findall(r'"volume": "(.*?)"',response.text)[0]
        except:
            volume = '7550.4'
        categroy_id_1 = re.findall(r'"categoryId":"(.*?)"',response.text)[0]
        categroy_id_2 = re.findall(r'"category2":"(.*?)"',response.text)[0]
        shop_type = re.findall(r'"shopType":"(.*?)"',response.text)[0]
        prdtype = re.findall(r'"prdType":"(.*?)"',response.text)[0]
        cluster_id = re.findall(r'"clusterId":"(.*?)"',response.text)[0]
        if prdtype == 'S':
            if sn_partNumber == sn_passpartnum:
                c = '1'
            else:
                c = '2'
        else:
            c = '0'
        _ = execjs.eval('new Date().getTime()')
        info_url = f'https://pas.suning.com/nspcsale_{c}_{sn_passpartnum}_{sn_partNumber}_{vendor_code}_20_021_0210199_157122_1000267_9264_12113_Z001___{procatecode}_1.48_0___000058759____0___{volume}_2_01_{categroy_id_2}_{categroy_id_1}_.html?_=' + str(_)
        yield scrapy.Request(info_url,callback=self.parse_goods_info_detail,meta={'item':item,'prdtype':prdtype,'vendor_code':vendor_code,'shop_type':shop_type,'sn_passpartnum':sn_passpartnum,'sn_partNumber':sn_partNumber,'cluster_id':cluster_id})

    def parse_goods_info_detail(self,response):
        item = response.meta['item']
        prdtype = response.meta['prdtype']
        vendor_code = response.meta['vendor_code']
        shop_type = response.meta['shop_type']
        sn_partNumber = response.meta['sn_partNumber']
        sn_passpartnum = response.meta['sn_passpartnum']
        cluster_id = response.meta['cluster_id']
        if prdtype.lower() == 's':
            originalCmmdtyType = 'style'
        elif prdtype.lower() == 't':
            originalCmmdtyType = 'package'
        else:
            originalCmmdtyType = 'general'
        all_data = re.findall(r'pcData\((.*)\)',response.text)[0]
        all_data = json.loads(all_data)
        item['goods_price'] = all_data['data']['price']['saleInfo'][0]['promotionPrice']
        try:
            item['goods_freight'] = all_data['data']['freightObj']['fare']
        except:
            item['goods_freight'] = '0.0'

        if prdtype.lower() == 's':
            partNumber = sn_passpartnum
        else:
            partNumber = sn_partNumber
        if shop_type == '-1':
            supplierCode = ''
        else:
            if shop_type == '0':
                supplierCode = '0000000000'
            else:
                supplierCode = vendor_code
        cmmdtyType = 'cluster' if cluster_id else originalCmmdtyType
        #cluster为查看各种种类的全部评论
        #general为查看当前种类当前商品的评论
        comment_url = 'https://review.suning.com/cluster_cmmdty_review/' + '-'.join([cmmdtyType, cluster_id, partNumber, supplierCode, '1', 'total']) + '.htm' + '?originalCmmdtyType=' + originalCmmdtyType
        item_copy = copy.deepcopy(item)
        yield scrapy.Request(comment_url,callback=self.parse_comment_info,meta={'item':item_copy})

    def parse_comment_info(self,response):
        item = response.meta['item']
        item['good_comments_num'] = int(response.xpath('//li[@data-type="good"]/@data-num').extract_first())
        item['bad_comments_num'] = int(response.xpath('//li[@data-type="bad"]/@data-num').extract_first())
        #data-type="total"
        item['all_comments_num'] = int(response.xpath('//li[@data-type="total"]/@data-num').extract_first())
        if item['all_comments_num']:
            item['good_rate'] = np.round(item['good_comments_num']/item['all_comments_num'],2)
            item['bad_rate'] = np.round(item['bad_comments_num']/item['all_comments_num'],2)
        else:
            item['good_rate'] = 0
            item['bad_rate'] = 0
        item['c_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        yield item



















