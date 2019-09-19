import requests
from lxml import etree
from requests.packages import urllib3
import time
import random

urllib3.disable_warnings()

PORXY_URL = 'https://www.xicidaili.com/nn/'
TARGET_URL = 'https://seat.lib.whu.edu.cn:8443/rest/auth'
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36'
}


def try_spider(url, proxy):
    """
    尝试利用指定proxy爬取目标url，成功则返回该proxy
    :param url: 目标url
    :param proxy: 指定使用的proxy
    :return: 返回能够使用的proxy
    """
    s = requests.session()
    s.trust_env = False
    s.verify = False
    s.headers = HEADERS
    try:
        content = s.get(url, headers=s.headers, proxies=proxy)
    except:
        print('连接出错！')
        return False

    if content.status_code == 200:
        print('尝试成功！')
        return True
    else:
        return False


def get_proxy(ip_pool_name):
    """
    从ip池获得一个随机的代理ip
    :param ip_pool_name: str,存放ip池的文件名,
    :return: 返回一个proxies字典,形如:{'HTTPS': '106.12.7.54:8118'}和组成proxy的基本元素
    """
    with open(ip_pool_name, 'r') as f:
        datas = f.readlines()
    id = random.randint(0, len(datas))
    ip = datas[id].strip().split(',')
    proxies = {ip[0].lower(): ip[0].lower() + '://' + ip[1] + ':' + ip[2]}
    proxy_list = [ip[0].upper(), ip[1], ip[2]]
    return proxies, proxy_list


def set_ip(proxy_list, mode='w+', file_name='success_ip.csv'):
    """
    将可使用的代理保存到相应文件
    :param ip:使用的proxy
    :return: 返回是否成功的布尔量
    """
    try:
        with open(file_name, mode) as f:
            f.write(','.join([proxy_list[0], proxy_list[1], proxy_list[2]]) + '\n')
        return True
    except:
        return False


def proxy_spider(pages=3500, max_change_porxies_times=300):
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/68.0.3440.75 Safari/537.36'
        }
        while True:
            content = s.get(url, headers=s.headers, proxies=proxies)
            time.sleep(random.uniform(1.5, 4))  # 每读取一次页面暂停一会,否则会被封
            if content.status_code == 503:  # 如果503则ip被封,就更换ip
                proxies = get_proxy('static_ips.csv')
                try_times += 1
                print(f'第{str(try_times):0>3s}次变更,当前{proxies}')
                if try_times > max_change_porxies_times:
                    print('超过最大尝试次数,连接失败!请手动更换static ip!')
                    return -1
                continue
            else:
                # 如果返回码是200 ,就跳出while循环,对爬取的页面进行处理
                break

        print(f'正在抓取第{i + 1}页数据,共{pages}页')
        cnt = 0
        for j in range(2, 102):  # 用简单的xpath提取http,host和port
            tree = etree.HTML(content.text)
            http = tree.xpath(f'//table[@id="ip_list"]/tr[{j}]/td[6]/text()')[0]
            host = tree.xpath(f'//table[@id="ip_list"]/tr[{j}]/td[2]/text()')[0]
            port = tree.xpath(f'//table[@id="ip_list"]/tr[{j}]/td[3]/text()')[0]
            # 检查提取的代理ip是否可用
            if try_spider(TARGET_URL, proxies):
                print('找到第'+str(cnt+1)+'个代理ip!')
                set_ip([http, host, port], 'a+', 'ips_pool.csv')
                cnt += 1
                if cnt > 20:
                    return True
                else:
                    continue
            else:
                continue


def fresh_proxy():
    """
    在代理多次失效的情况下，刷新ips_pool.csv内的代理
    :return:
    """
    # 从根部静态ip池内提取代理ip
    proxy = get_proxy('static_ips.csv')

    res = False
    fail_cnt = 0
    while not res:
        fail_cnt += 1

        # 失败次数过多
        if fail_cnt > 25:
            print('二级代理刷新失败，请手动更新static_ips.csv!')
            return False
        # 常规爬取西刺网ip
        res = try_spider(PORXY_URL, proxy)
        if res:
            res = proxy_spider()
            print('ips_pool更新完成!')
            return True
        else:
            fail_cnt += 1
            continue


if __name__ == '__main__':
    res = False
    fail_cnt = 0
    print('start finding proxy_ip...')

    while not res:
        fail_cnt += 1
        # 失败次数过多，更换ips_pool内代理
        if fail_cnt > 20:
            print('失败次数过多，start更换ips_pool内代理！')
            if not fresh_proxy():
                exit(10)

        # 常规爬取
        print('start spider normally...')
        proxy, proxy_list = get_proxy('ips_pool.csv')
        res = try_spider(TARGET_URL, proxy)
        if not res:
            print('fail!The time is:'+str(fail_cnt))
            fail_cnt += 1
            continue
        else:
            print('保存可访问的代理ip...')
            res = set_ip(proxy_list)
            continue
    print('成功获取可访问目标网站的代理ip!')
    exit(0)
