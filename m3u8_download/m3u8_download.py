# -*- coding: utf-8 -*-
import os,sys
import time
import m3u8
import requests
from glob import iglob
from natsort import natsorted
from urllib.parse import urljoin
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from aes_encrypt import *

import json

def hexstr2bytes(hex_str):
    hex_dic = {"0":0, "1":1, "2":2, "3":3, 
               "4":4, "5":5, "6":6, "7":7, 
               "8":8, "9":9, "A":10,"B":11,
               "C":12,"D":13,"E":14,"F":15}
    
    hex_str = hex_str.split("0x")[-1]
    if(len(hex_str) % 2):
        hex_str = "0%s"% hex_str
    
    hex_str = hex_str.upper()
    
    n_list = []   
    str_len = len(hex_str)
    for i in range(int(str_len/2)):
        n = hex_dic[hex_str[i*2]] * 16 + hex_dic[hex_str[i*2+1]]
        n_list.append(n)
    
    return bytes(n_list)

@dataclass
class DownLoad_M3U8(object):
    m3u8_url  : str
    file_name : str
    #base_uri  : str
    '''
    def __init__(self, *args, **kwargs):
        self.base_url = None
        self.key = None
        self.iv = None
        self.m3u8_url = args[0]
        self.file_name = args[1]
        #print (args)
    '''
    def __post_init__(self):
        self.headers   = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',}
        self.threadpool = ThreadPoolExecutor(max_workers=3)
        if not self.file_name:
            self.file_name = 'new.mp4'
        self.base_url = None
        self.key = None
        self.iv = None      
        self.save_path = "downloaded/"
        try:
            os.mkdir(self.save_path)
        except FileExistsError :
            pass
        except:
            raise

    def get_ts_url(self):
        m3u8_obj = m3u8.load(self.m3u8_url)
        base_uri = m3u8_obj.base_uri
        print (dir(m3u8_obj) )
        print (m3u8_obj.data)
        print (m3u8_obj.keys)
        for seg in m3u8_obj.segments:
            yield urljoin(base_uri,seg.uri)
    
    def get_ts_segment(self):
        m3u8_obj = m3u8.load(self.m3u8_url)
        self.base_uri = m3u8_obj.base_uri
        #print (m3u8_obj.keys)
        #print (m3u8_obj.segments)
        #print (m3u8_obj.data)
        print ("totals %d"%len(m3u8_obj.data["segments"]))
        '''
        f = open("data.json", "wb")
        f.write(json.dumps(m3u8_obj.data).encode())
        f.close()
        '''
        for seg in m3u8_obj.data["segments"]:
            yield seg       
    
        
    def download_single_ts(self,urlinfo):
        url,ts_name = urlinfo
        res = requests.get(url,headers = self.headers)
        with open(ts_name,'wb') as fp:
            fp.write(res.content)

    def download_single_ts2(self, ts_info):
        try:
            seg,ts_name = ts_info
            url = urljoin(self.base_uri,seg["uri"])
            res = requests.get(url,headers = self.headers)
            with open(ts_name,'wb') as fp:
                fp.write(res.content)
            
            
            #decrypt
            if ("key" in seg.keys()):
                method = seg["key"]["method"]   # "AES-128"
                key_uri = seg["key"]["uri"]
                iv = seg["key"]["iv"]           # "0x00000000000000000000000000000000"
                
                # iv proc
                iv = hexstr2bytes(iv)
                
                #print (iv)
                res = requests.get(key_uri, headers=self.headers)
                key = res.content
                self.iv = iv
                self.key = key
                
            
                ts_file = open(ts_name, "rb")
                data = ts_file.read()
                ts_file.close() 
                
                decrypt_data = decrypt(data, key, iv)
                ts_out = "%s-decrypt"%(ts_name)
                out_file = open(ts_out, "wb")
                out_file.write(decrypt_data)
                out_file.close() 
                
                os.remove(ts_name)
                os.rename(ts_out, ts_name)
        except Exception as e:
            print ("download error:%s"%e)
        
    def download_all_ts(self):
        '''ts_urls = self.get_ts_url()
        for index,ts_url in enumerate(ts_urls):
            print (ts_url)
            self.threadpool.submit(self.download_single_ts,[ts_url,f'{index}.ts'])
            '''
        ts_segs = self.get_ts_segment()
        for index,ts_seg in enumerate(ts_segs):
            save_name = "%s/%d.ts"%(self.save_path, index)
            if (os.path.exists(save_name)):
                print ("%s exist"%save_name)
                continue
            print ("%d\r"%(index+1), end='')
            #self.threadpool.submit(self.download_single_ts2,[ts_seg,f'{index}.ts'])
            self.threadpool.submit(self.download_single_ts2,[ts_seg, save_name])
            pass  
        print ("\n")
        self.threadpool.shutdown()

    def run(self):
        self.download_all_ts()
        ts_path = '%s/*.ts'%self.save_path
        with open(self.file_name,'wb') as fn:
            for ts in natsorted(iglob(ts_path)):
                with open(ts,'rb') as ft:
                    scline = ft.read()
                    fn.write(scline)
        for ts in iglob(ts_path):
            #os.remove(ts)
            pass

if __name__ == '__main__':
    m3u8_url = ''
    file_name = ''
    
    try:
        m3u8_url = sys.argv[1]
        file_name = sys.argv[2]
    except:
        pass
    
    try:
        fp = open("m3u8_url.txt", "rb")
        m3u8_url = fp.read()
        fp.close()
        m3u8_url = bytes.decode(m3u8_url) 
        m3u8_url = m3u8_url.strip('\r\n\t ')
    except Exception as e:
        print ("open m3u8_url.txt error:%s"%e)
    print ("m3u8 : %s"%m3u8_url)
    print ("filename : %s"%file_name)
    
    start = time.time()

    M3U8 = DownLoad_M3U8(m3u8_url,file_name)
    M3U8.run()

    end = time.time()
    print ('use time %f'%(end - start))