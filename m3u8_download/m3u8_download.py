# -*- coding: utf-8 -*-
import os,sys
import time
import m3u8
import requests
import re
from glob import iglob
from natsort import natsorted
from urllib.parse import urljoin
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
#from .aes_encrypt import *
import aes_encrypt

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
'''
def valid_url(url):
    pattern=re.match(r'(http|ftp|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?',url,re.IGNORECASE)
    if pattern:
        return True
    
    return False
'''    
        
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
        self.headers   = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',}
        self.threadpool = ThreadPoolExecutor(max_workers=3)
        if not self.file_name:
            self.file_name = 'm3u8new.mp4'
        self.base_url = None
        self.key = None
        self.iv = None  
        self.key_uri = None
        self.save_path = "m3u8downloaded/"
        self.total_segments = 0
        try:
            os.mkdir(self.save_path)
        except FileExistsError :
            pass
        except:
            raise

    def get_first_key(self, seg):
        if ("key" in seg.keys()):
            key_uri_src = seg["key"]["uri"]
            key_uri = urljoin(self.base_uri, key_uri_src)
                
            try:
                res = requests.get(key_uri, headers=self.headers)
            except Exception as e:
                print ("get key error: url=%s, %s, get_key %s"%(key_uri,e, ts_name))  
                return None
            
            key = res.content
            if (len(key) > 100):
                print ("key len > 100,")
                return None
            self.key = key
            self.key_uri = key_uri_src
        
        return self.key
            
    def get_ts_segment(self):
        m3u8_obj = m3u8.load(self.m3u8_url, timeout=10)
        self.base_uri = m3u8_obj.base_uri
        #print (m3u8_obj.keys)
        #print (m3u8_obj.segments)
        #print (m3u8_obj.data)
        print ("totals %d"%len(m3u8_obj.data["segments"]))
        self.total_segments = len(m3u8_obj.data["segments"])
        '''
        f = open("data.json", "wb")
        f.write(json.dumps(m3u8_obj.data).encode())
        f.close()
        '''
        self.get_first_key(m3u8_obj.data["segments"][0])
        for seg in m3u8_obj.data["segments"]:
            yield seg       
    
    def download_single_ts2(self, ts_info):
        try:
            seg,ts_name = ts_info
            #download key
            if ("key" in seg.keys()):
                key_uri_src = seg["key"]["uri"]
                if (key_uri_src == self.key_uri):
                    key = self.key
                else:
                    print ("debug: get key from ")
                    
                    #if (valid_url(key_uri_src) == False):
                    #    key_uri = urljoin(self.base_uri, key_uri_src)
                    key_uri = urljoin(self.base_uri, key_uri_src)
                        
                    try:
                        res = requests.get(key_uri, headers=self.headers)
                    except Exception as e:
                        print ("get key error: url=%s, %s, get_key %s"%(key_uri,e, ts_name))  
                        return
                    
                    key = res.content
                    if (len(key) > 100):
                        print ("key len > 100,")
                        return
                    self.key = key
                    #self.key_uri = key_uri_src
            
            #download ts
            url = urljoin(self.base_uri,seg["uri"])
            res = requests.get(url,headers = self.headers, timeout=5)
            with open(ts_name,'wb') as fp:
                fp.write(res.content)
            
            
            #decrypt
            if ("key" in seg.keys()):
                method = seg["key"]["method"]   # "AES-128"
                
                iv = None
                if ("iv" in seg["key"].keys()):
                    iv = seg["key"]["iv"]           # "0x00000000000000000000000000000000"
                
                    # iv proc
                    iv = hexstr2bytes(iv)
                
                
                self.iv = iv
                
            
                ts_file = open(ts_name, "rb")
                data = ts_file.read()
                ts_file.close() 
                
                decrypt_data = aes_encrypt.decrypt(data, key, iv)
                ts_out = "%s-decrypt"%(ts_name)
                out_file = open(ts_out, "wb")
                out_file.write(decrypt_data)
                out_file.close() 
                
                os.remove(ts_name)
                os.rename(ts_out, ts_name)
        except Exception as e:
            print ("download_single_ts2 download %s error:%s"%(ts_name,e))
            try:
                print ("key=%s,==="%key)
            except:
                pass
            time.sleep(10)
        
    def download_all_ts(self):
        ts_segs = self.get_ts_segment()
        for index,ts_seg in enumerate(ts_segs):
            n1 = int((index+1)*50/self.total_segments)
            n2 = 50-n1
            
            print ("\r├%s%s┤ %f%%"%("#"*n1, " "*n2, (index+1)*100/self.total_segments), end='')
            
            save_name = "%s/%d.ts"%(self.save_path, index)
            if (os.path.exists(save_name)):
                #print ("%s exist"%save_name)
                continue
            while (self.threadpool._work_queue.qsize() > 1):
                time.sleep(1)
            #print ("%d\r"%(index+1), end='')
            
            self.threadpool.submit(self.download_single_ts2,[ts_seg, save_name])
            #print ("\n")
            #print (json.dumps(ts_seg))
            #break
            pass  
        print ("\n")
        self.threadpool.shutdown()

    def run(self):
        print ("downloading...")
        self.download_all_ts()
        print ("merging...")
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