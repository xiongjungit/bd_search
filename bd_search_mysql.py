#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
@author: XiongJun
@file: bd_search_mysql.py
@time: 2017/5/12 11:47

程序说明: 使用python+selenium+webdriver操作浏览器进行百度搜索,将搜索结果保存到文件中

css元素选择器
    <div id="content_left">
	    <div class="result c-container " id="1" srcid="1599" tpl="se_com_default">
		    <h3 class="t">
			    <a href="http://www.baidu.com/link?url=N1-VEpaLsZKbqvAYhVvdf19sHp-f9M5-wDinFvSJnalyQGQ7KDZsr3ZYGiB81XG2F-qCbIFUlhsJS3yHjTdtC_" target="_blank">功能自动化测试工具——<em>Selenium</em>篇</a>
		    </h3>
	    </div>
    </div>

1.选择顶层div标签 （#content_left)
2.选择第2层div标签 （#content_left .result.c-container)或者(#(1-50))
3.选择第3层h3标签 （#content_left .result.c-container .t)


PhantomJS 是一个基于 WebKit 的服务器端 JavaScript API。
它全面支持web而不需浏览器支持，其快速，原生支持各种Web标准： DOM 处理, CSS 选择器, JSON, Canvas, 和 SVG。
PhantomJS 可以用于 页面自动化 ， 网络监测 ， 网页截屏 ，以及 无界面测试 等。
'''



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pyquery import PyQuery as pq
import MySQLdb
import time,re,sys,os


# 设置字符集
reload(sys)
sys.setdefaultencoding('utf-8')

# 定义搜索关键字
# keywords = u'python 教程'
keywords = u'python 爬虫'
# keywords = u'python selenium'
# keywords = u'自动化测试'
# keywords = u'安全测试'
# keywords = u'渗透测试'

# 定义搜索到第几页
lastpage = 6

# 定义数据列表
data = []

# 定义浏览器对象
driver = webdriver.Chrome() # 测试通过
# driver = webdriver.Firefox() # 测试不通过
# driver = webdriver.PhantomJS() # 测试不通过

# 定义页面超时时间(10秒)
wait = WebDriverWait(driver, 10)

#滚动条滚动到页面底部
def wpb_scroll():
    # 定义页面滚动条位置
    js = "window.scrollBy(0,document.body.scrollHeight)"
    # 执行页面滚动条滚动
    driver.execute_script(js)

#打开百度搜索关键词，并进行搜索设置
def bd_search():
    try:
        # 浏览器窗口最大化
        driver.maximize_window()

        # 模拟浏览器打开百度搜索
        driver.get("http://www.baidu.com")

        # url
        url = driver.current_url
        # 标题
        title = driver.title
        # 备案信息
        icp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#cp"))).text


        # 查找页面的“设置”选项，并进行点击
        driver.find_elements_by_link_text(u'设置')[0].click()
        # 打开设置后找到“搜索设置”选项，并进行点击
        driver.find_elements_by_link_text(u'搜索设置')[0].click()
        time.sleep(3)
        # # 点击“仅简体中文”
        driver.find_element_by_css_selector("#se-settting-2 > label:nth-child(4)").click()
        time.sleep(3)
        # 设置为每页显示50条
        m = driver.find_element_by_id('nr')
        time.sleep(3)
        m.find_element_by_xpath('//*[@id="nr"]/option[3]').click()
        time.sleep(3)
        # 在弹出的警告页面点击确定
        driver.find_element_by_class_name("prefpanelgo").click()
        time.sleep(3)
        driver.switch_to_alert().accept()
        time.sleep(3)

        # 打印百度搜索相关信息
        print "\n"
        print "百度搜索:\n"
        print "页面地址:    %s " % url
        print "页面标题:    %s " % title
        print "备案信息:    %s " % (icp[25:37:] + icp[38:60:])
        print "搜索设置:    仅简体中文 "
        print "搜索设置:    每页显示50条 "
        print "关 键 字:    %s" % keywords
        print "\n"
        print "开始爬取数据，请稍候...\n"


        # 输入框
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#kw")))
        #'百度一下'按钮
        submit = wait.until( EC.element_to_be_clickable((By.CSS_SELECTOR,"#su")))

        # 模拟浏览器输入关键字
        input.send_keys(keywords)
        # 模拟点击'百度一下'按钮
        submit.click()
        wpb_scroll()
        time.sleep(3)
    except TimeoutException:
        print "请求页面超时，正在重试..."
        bd_search()

# 获取索引页内容
def index_page():
    # 等待条件
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#content_left"))) #等待搜索结果页面左侧搜索结果加载完成
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#content_left .result.c-container"))) #等待搜索结果页面左侧搜索结果列表加载完成
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#content_left .result.c-container .t"))) #等待搜索结果页面左侧搜索结果列表元素加载完成
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,"#page"))) #等待搜索结果页面底部翻页条加载完成
    html = driver.page_source #返回网页源码
    content = pq(html) # 使用pyquery解析网页内容
    reg = re.compile(r' href="(.*?)" target="_blank">.*</a>')


    page = []
    id_start = []
    id_end = []

    # 搜索起始页
    for pagenum in range(1, 101):
        page.append(pagenum)
    # 索引页搜索结果编号规律(1-50,51-100,101-150,151-200....)(一页显示50条搜索结果)
    for start in range(0, 10001, 50):
        id_start.append(start + 1)
    for end in range(50, 10001, 50):
        id_end.append(end + 1)

    # 将对象中对应的元素按顺序组合成一个tuple
    idxs = zip(id_start, id_end)
    array = zip(page, idxs)

    # 当前页码
    pagenumber = int(driver.find_element_by_css_selector("#page > strong > span.pc").text)
    print "[正在爬取第 %s 页数据...]\n" % pagenumber

    # 如果当前页码是1，那么搜索结果编号就是1-50；如果当前页码是2，那么搜索结果编号就是51-100...依次类推。
    """
    第1页 1-50
    第2页 51-100
    第3页 101-150
    ...
    """
    for i in array:
        if pagenumber == i[0]:
            ids = range(i[1][0],i[1][1])
            for idx in ids:
                title  = content('#content_left #%s .t' % idx).text() #标题
                prelink = content('#content_left #%s .t' % idx).html() #待处理带链接和标题的html页面
                link = str(re.findall(reg,str(prelink)))[2:-2] #根据正则表达式匹配到的链接地址
                data.append((title,link))
    return data

# 翻页并获取索引页内容
def get_data():
    try:
        index_page()
        page2 = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#page > a.n")))
        page2.click()
        wpb_scroll()
        time.sleep(3)
        index_page()
        while True:
            nextpage = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#page > a:nth-child(12)")))
            nextpage.click()
            wpb_scroll()
            time.sleep(3)
            index_page()
            pagenumber = int(driver.find_element_by_css_selector("#page > strong > span.pc").text)
            # 一共搜索多少页
            # if pagenumber >= lastpage:
            #     break
    except TimeoutException:
        print "爬取总页数: ",pagenumber
        print "\n"
        return pagenumber

#搜索结果保存到数据库
def result_db(data):
    try:
        # 连接数据库
        db = MySQLdb.connect(host="192.168.56.254",user="root",passwd="root",charset="utf8")

        # 获取操作游标
        cursor = db.cursor()

        # 创建数据库
        # sql = """CREATE DATABASE IF NOT EXISTS bd_search DEFAULT CHARSET utf8 COLLATE utf8_general_ci;"""
        # cursor.execute(sql)
        # db.commit()

        # 选择数据库
        db.select_db('bd_search')


        # 创建表
        # sql = """DROP TABLE IF EXISTS `result`; \
        #     CREATE TABLE `result` ( \
        #     `id` int(11) NOT NULL AUTO_INCREMENT,\
        #     `keywords` varchar(255) CHARACTER SET utf8mb4 NOT NULL, \
        #     `title` varchar(255) CHARACTER SET utf8mb4 NOT NULL, \
        #     `link` varchar(255) NOT NULL, \
        #     PRIMARY KEY (`id`) \
        #     ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""
        # cursor.execute(sql)
        # db.commit()

        # 清空表
        # cursor.execute("delete from result")
        # db.commit()

        # 写入result表
        for title,link in data: # 取数据
            cursor.execute("""insert into result(keywords,title,link) values(%s,%s,%s) """,(keywords,title,link))
            db.commit()
            # print "关键字: ",keywords
            # print "标  题: ",title
            # print "链  接: ",link
            # print "\n"
        cursor.close()#关闭连接，释放资源
    except:
        # 发生错误时回滚
        db.rollback()

def main():
    try:
        print "程序运行中,请稍候...\n"
        bd_search()
        totalpage = int(get_data()) # 总页数
        print "搜索结果: \n"
        print "[一共 %s 页 %s 条搜索结果]\n" % (totalpage,totalpage*50)
        print "[保存搜索结果到数据库...]\n"
        result_db(data)
    finally:
        print "程序运行完毕，即将关闭...\n"
        time.sleep(3)
        driver.close()  # 关闭浏览器标签

if __name__ == "__main__":
    main()
