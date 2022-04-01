# -*- coding: utf-8 -*-
import os,sys
import time
import m3u8
import requests
import re
from glob import iglob
from natsort import natsorted
from urllib.parse import urljoin,urlparse
#from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
#from .aes_encrypt import *
import aes_encrypt
import subprocess

import json

import logging

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
        
#@dataclass
class DownLoad_M3U8(object):
    #m3u8_url  : str
    #file_name : str
    
    def __init__(self, m3u8_url, file_name = ""):
        self.m3u8_url = m3u8_url
        self.file_name = file_name
        self.headers   = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
                          'accept-encoding': 'gzip, deflate, br',
                          #'referer': 'https://vod.bunediy.com/share/hiAB0dgxRvsc3I04',
                          #'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
                          }
        self.max_workers = 1
        self.threadpool = ThreadPoolExecutor(max_workers=self.max_workers)
        if not self.file_name:
            self.file_name = 'm3u8new.ts'
        self.base_url = None
        self.key = None
        self.iv = None  
        self.key_uri = None
        self.save_path = "%s-downloaded/"%(self.file_name)
        self.total_segments = 0
        self.failed_count = 0
        self.success_count = 0
        
        try:
            os.mkdir(self.save_path)
        except FileExistsError :
            pass
        except:
            raise

    def get_first_key(self, seg):
        if ("key" in seg.keys()):
            key_uri_src = seg["key"]["uri"]
            
            if (os.path.isfile(self.base_uri)):
                if(not os.path.isabs(key_uri_src)):
                    key_uri = self.base_uri + key_uri_src
                else:
                    key_uri = key_uri_src
                with open(key_uri, 'rb') as fp:
                    key = fp.read()
            else:           
                key_uri = urljoin(self.base_uri, key_uri_src)
                
                for i in range(3):
                    try:
                        res = requests.get(key_uri, headers=self.headers, timeout=3)
                        #print ("get first key :%s"%res.content)
                    except Exception as e:
                        print ("get key error: url=%s, %s, get_key"%(key_uri,e)) 
                        # sys.exit(1)
                        if i >= 2 :
                            return None
                        continue                        
            
                key = res.content
            if (len(key) > 100):
                print ("key len > 100,")
                return None
            self.key = key
            self.key_uri = key_uri_src
        
        return self.key
            
    def get_ts_segment(self, m3u8_obj):
        '''
        f = open("data.json", "wb")
        f.write(json.dumps(m3u8_obj.data).encode())
        f.close()
        '''
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
                    print ("key_uri=%s"%key_uri) 
                    print ("self.base_uri=%s"%self.base_uri)
                    try:
                        res = requests.get(key_uri, headers=self.headers, timeout=3)
                        print ("get key: %s\n"%res.content)
                    except Exception as e:
                        print ("get key error: url=%s, %s, get_key %s"%(key_uri,e, ts_name))  
                        return
                    
                    key = res.content
                    if (len(key) > 100):
                        print ("key len > 100,")
                        return
                    self.key = key
                    self.key_uri = key_uri_src
            
            #download ts
            url = urljoin(self.base_uri,seg["uri"])
            res = requests.get(url,headers = self.headers, timeout=4)
            with open(ts_name,'wb') as fp:
                fp.write(res.content)
            
            
            #decrypt
            try:
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
                print ("\ndownload_single_ts2 decrypt :%s"%e)
                os.remove(ts_name)
                self.failed_count += 1
        except requests.exceptions.ReadTimeout as e:
            #print ("\ndownload_single_ts2 ReadTimeout :%s"%e)
            self.failed_count += 1
        except requests.exceptions.ConnectionError as e:
            self.failed_count += 1
            time.sleep(0.5)
        except Exception as e:
            print ("  download_single_ts2 download %s error:%s"%(ts_name,e))
            print ("class name=%s"%(e.__class__.__name__))
            self.failed_count += 1
            time.sleep(2)
    
    def print_progress_old(self, index):
        n1 = int((index+1)*50/self.total_segments)
        n2 = 50-n1
        f_perc = 0
        if (index > 0):
            f_perc = self.failed_count*100/index
        print ("\r├%s%s┤ %.2f%%  FAILED:%d(%.2f%%)"%("#"*n1, " "*n2, (index+1)*100/self.total_segments, self.failed_count, f_perc), end='')
    
    def print_progress(self, count):
        n1 = int(count*50/self.total_segments)
        n2 = 50-n1
        f_perc = 0
        if (count > 0):
            f_perc = self.failed_count*100/count
        print ("\r├%s%s┤ %.2f%%  FAILED:%d(%.2f%%)"%("#"*n1, " "*n2, (count)*100/self.total_segments, self.failed_count, f_perc), end='')
        
    def download_all_ts(self):
        for i in range(0,3):
            try:
                m3u8_obj = m3u8.load(self.m3u8_url, timeout=3, headers=self.headers)
                m3u8_obj.dump("%s/tmp.m3u8"%self.save_path)
            except Exception as e:
                print ("get m3u8 info error: %s"%e)
                logging.exception("get m3u8 info error")
                if (i >= 2):
                    raise
                continue
            break 
        
        print ("totals %d"%len(m3u8_obj.data["segments"]))
        self.base_uri = m3u8_obj.base_uri
        #print (m3u8_obj.keys)
        #print (m3u8_obj.segments)
        #print (m3u8_obj.data)
        
        self.total_segments = len(m3u8_obj.data["segments"]) 
        if(self.total_segments == 0):
            print("m3u8 segments len = 0")
            return;
        self.get_first_key(m3u8_obj.data["segments"][0])
        if (self.key == b''):
            return []
        
        #save base_url and key
        with open("%s/infomation.txt"%self.save_path, "wb") as f:
            f.write(("url=%s\n"%(self.m3u8_url)).encode())
            f.write(("segments=%d\n"%(self.total_segments)).encode())
            f.write(("base_uri=%s\n"%(m3u8_obj.base_uri)).encode())
            if(self.key):
                f.write(("key=%s"%(self.key.hex())).encode())
        
        for i in range(0, 3):
            _count = 0
            tmp_count = 0
            last_features = [None for i in range(0, self.max_workers)]
            ts_segs = self.get_ts_segment(m3u8_obj)
            self.failed_count = 0
            for index,ts_seg in enumerate(ts_segs):
                '''
                n1 = int((index+1)*50/self.total_segments)
                n2 = 50-n1
                f_perc = 0
                if (index > 0):
                    f_perc = self.failed_count*100/index
                print ("\r├%s%s┤ %.2f%%  FAILED:%d(%.2f%%)"%("#"*n1, " "*n2, (index+1)*100/self.total_segments, self.failed_count, f_perc), end='')
                '''
                save_name = "%s/%d.ts"%(self.save_path, index)
                if (os.path.exists(save_name)):
                    #print ("%s exist"%save_name)
                    _count += 1
                    #self.print_progress(_count)
                    continue
                while (self.threadpool._work_queue.qsize() > 0):
                    time.sleep(1)
                #print ("%d\r"%(index+1), end='')
                tmp_count += 1
                f = self.threadpool.submit(self.download_single_ts2,[ts_seg, save_name])
                last_features[tmp_count%self.max_workers] = f
                #if (index > self.max_workers):
                #    self.print_progress(index-self.max_workers)
                
                
                if (tmp_count > self.max_workers + 1):
                    _count += 1
                    self.print_progress(_count)
                #print ("add %d, qsize=%d\n"%(tmp_count, self.threadpool._work_queue.qsize()))
                  
            for i in range(15):
                all_done = True
                done_count = 0
                for f in last_features:
                    if (f != None):
                        if (f.done()):
                            done_count +=1
                        else:
                            all_done = False
                            time.sleep(1)
                            break
                if (all_done):
                    break
            
            self.print_progress(self.total_segments)
            print ("")
            print ("debug: all-%d,done-%d, i=%d,done_count=%d"%(self.total_segments, done_count+_count,i, done_count))
            if (self.failed_count == 0):
                break
            print("Failed to download %d segment(s), try again!"%(self.failed_count))
            
        self.threadpool.shutdown()
        
        
        if (self.failed_count > 0):
            print ("Failed to download some segments, %d"%(self.failed_count))

    def run(self):
        t_start = time.time()
        print ("downloading...")
        self.download_all_ts()
        if (os.path.exists("output-%s.mp4"%(self.file_name))):
            print ('output-%s.mp4 is exists, pass'%(self.file_name))
            return
        
        print ("merging...")
        
        ts_path = '%s/*.ts'%self.save_path

        file_num = 0
        with open(self.file_name,'wb') as fn:
            for ts in natsorted(iglob(ts_path)):
                with open(ts,'rb') as ft:
                    scline = ft.read()
                    fn.write(scline)
                    file_num += 1
        '''
        with open('filelist.txt','wb') as fn:
            for ts in natsorted(iglob(ts_path)):
                fn.write(("file \'%s\'\n"%ts).encode())        
        for ts in iglob(ts_path):
            #os.remove(ts)
            break
        subprocess.run('ffmpeg -v 16 -y -f concat -safe 0 -i filelist.txt -c copy output-%s.mp4'%(self.file_name))
        '''
        print ("download %d file(s). use %f seconds"%(file_num, time.time() - t_start))

if __name__ == '__main__':
    m3u8_url = ''
    file_name = ''
    m3u8_url_list = []
    
    try:
        m3u8_url = sys.argv[1]
        file_name = sys.argv[2]
    except:
        pass
    
    try:
        with open("m3u8_url.txt", "rb") as fp:
            while True:
                u = fp.readline()
                if (not u):
                    break
                if (u.startswith(b'#')):
                    continue
                m3u8_url = bytes.decode(u, encoding="gbk")
                m3u8_url = m3u8_url.strip('\r\n\t ')
                m3u8_url_list.append(m3u8_url)
        
    except Exception as e:
        print ("open m3u8_url.txt error:%s"%e)
    
    start = time.time()

    for index,m3u8_item in enumerate(m3u8_url_list):
        print ("\n==============================")
        print ("download %s"%m3u8_item)
        file_name = "m3u8-%d"%index
        M3U8 = DownLoad_M3U8(m3u8_item,file_name)
        M3U8.run()

    end = time.time()
    print ('use time %f'%(end - start))