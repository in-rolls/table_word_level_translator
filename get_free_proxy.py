#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from lxml.html import fromstring


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


if __name__ == "__main__":

    proxies = get_proxies()
    ok_proxies = []
    url = 'https://httpbin.org/ip'
    for i, proxy in enumerate(proxies):
        print("Checking #{:d}: {!s}".format(i + 1, proxy))
        try:
            response = requests.get(url,proxies={"http": proxy, "https": proxy}, timeout=5)
            print(response.json())
            ok_proxies.append(proxy)
        except KeyboardInterrupt:
            break
        except:
            #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
            #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 
            print("- Skipping. Connnection error")

    for proxy in ok_proxies:
        print(proxy)
