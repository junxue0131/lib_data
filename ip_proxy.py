import requests
from lxml import etree
from requests.packages import urllib3
import random, time
import os

urllib3.disable_warnings()

headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'User-Agent': 'doSingle/11 CFNetwork/893.14.2 Darwin/17.3.0',
                        'token': ''}


def spider(pages, max_change_porxies_times=300, target_url='https://seat.lib.whu.edu.cn:8443/rest/auth', file_name='ips_pool.csv'):
    """
    抓取 XiciDaili.com 的 http类型-代理ip-和端口号
    将所有抓取的ip存入 raw_ips.csv 待处理, 可用 check_proxies() 检查爬取到的代理ip是否可用
    -----
    :param pages:要抓取多少页
    :return:无返回
    """
    s = requests.session()
    s.trust_env = False
    s.verify = False
    urls = 'https://www.xicidaili.com/nn/{}'
    proxies = {}
    try_times = 0
    for i in range(100):
        i = random.randint(1, 100)
        url = urls.format(i + 1)
        s.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': urls.format(i if i > 0 else ''),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36'}
        while True:
            content = s.get(url, headers=s.headers, proxies=proxies)
            time.sleep(random.uniform(1.5, 4))  # 每读取一次页面暂停一会,否则会被封
            if content.status_code == 503:  # 如果503则ip被封,就更换ip
                if target_url == 'https://www.xicidaili.com/nn/' and file_name == 'ips_pool_t.csv':
                    proxies = get_proxies('static_ips.csv')    
                else:
                    proxies = get_proxies()
                try_times += 1
                print(f'第{str(try_times):0>3s}次变更,当前{proxies}')
                if try_times > max_change_porxies_times:
                    print('超过最大尝试次数,连接失败!')
                    return -1
                continue
            else:
                break  # 如果返回码是200 ,就跳出while循环,对爬取的页面进行处理

        print(f'正在抓取第{i+1}页数据,共{pages}页')
        cnt = 0
        for j in range(2, 102):  # 用简单的xpath提取http,host和port
            tree = etree.HTML(content.text)
            http = tree.xpath(f'//table[@id="ip_list"]/tr[{j}]/td[6]/text()')[0]
            host = tree.xpath(f'//table[@id="ip_list"]/tr[{j}]/td[2]/text()')[0]
            port = tree.xpath(f'//table[@id="ip_list"]/tr[{j}]/td[3]/text()')[0]
            if check_proxies(http, host, port, test_url=target_url, file_name=file_name):  # 检查提取的代理ip是否可用
                print('from ip_proxy:find correct ip!')
                cnt += 1
                if cnt > 20:
                    return True
                else:
                    continue
            else:
                continue


def check_proxies(http, host, port, file_name, test_url='https://seat.lib.whu.edu.cn:8443/rest/auth'):
    """
    检测给定的ip信息是否可用

    根据http,host,port组成proxies,对test_url进行连接测试,如果通过,则保存在 ips_pool.csv 中
    :param http: 传输协议类型
    :param host: 主机
    :param port: 端口号
    :param test_url: 测试ip
    :return: None
    """
    proxies = {http.lower(): http.lower() + '://' + host + ':' + port}
    print("测试：")
    print(proxies)
    try:
        res = requests.get(test_url, proxies=proxies, headers=headers, timeout=5, verify=False)
        print(res.text)
        if res.status_code == 200:
            print(f'{proxies}检测通过')
            if file_name == 'ips_pool_t.csv':
                with open('ips_pool_t.csv', 'a+') as f:
                    f.write(','.join([http, host, port]) + '\n')
            else:    
                with open(file_name, 'w') as f:
                    f.write(','.join([http, host, port]) + '\n')
            return True
    except Exception as e:  # 检测不通过,就不保存,别让报错打断程序
        print(f'{proxies}检测不通过')
        return False


def check_local_ip(fn, test_url):
    """
    检查存放在本地ip池的代理ip是否可用

    通过读取fn内容,加载每一条ip对test_url进行连接测试,链接成功则储存在 ips_pool.csv 文件中
    :param fn: filename,储存代理ip的文件名
    :param test_url: 要进行测试的ip
    :return: None
    """
    with open(fn, 'r') as f:
        datas = f.readlines()
        ip_pools = []
    for data in datas:
        # time.sleep(1)
        ip_msg = data.strip().split(',')
        http = ip_msg[0]
        host = ip_msg[1]
        port = ip_msg[2]
        proxies = {http: host + ':' + port}
        try:
            res = requests.get(test_url, proxies=proxies, timeout=2)
            if res.status_code == 200:
                ip_pools.append(data)
                print(f'{proxies}检测通过')
                with open('ips_pool.csv', 'a+') as f:
                    f.write(','.join([http, host, port]) + '\n')
        except Exception as e:
            print(e)
            continue


def get_proxies(ip_pool_name='ips_pool_t.csv'):
    """
    从ip池获得一个随机的代理ip
    :param ip_pool_name: str,存放ip池的文件名,
    :return: 返回一个proxies字典,形如:{'HTTPS': '106.12.7.54:8118'}
    """
    with open(ip_pool_name, 'r') as f:
        datas = f.readlines()
    ran_num = random.choice(datas)
    ip = ran_num.strip().split(',')
    proxies = {ip[0].lower(): ip[0].lower()+'://'+ip[1] + ':' + ip[2]}
    return proxies


def refresh_temp_ip():
    # 清空ips_pool_t.csv:
    with open('ips_pool_t.csv', 'w') as f:
        f.write('')
    spider(pages=3400, target_url='https://www.xicidaili.com/nn/', file_name='ips_pool_t.csv')
    # 校验ips_pool_t.csv是否为空,为空则继续进行
    while os.path.getsize('ips_pool_t.csv') == 0:
        with open('ips_pool_t.csv', 'w') as f:
            f.write('')
        spider(pages=3400, target_url='https://www.xicidaili.com/nn/', file_name='ips_pool_t.csv')
    



if __name__ == '__main__':
    if int(time.time()) % 5 == 0:
        refresh_temp_ip()
    t1 = time.time()
    res = spider(pages=3400)
    t2 = time.time()
    print('抓取完毕,时间:', t2 - t1)
    if res == True:
        exit(0)
    else:
        exit(10)
