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
from concurrent.futures import ThreadPoolExecutor, as_completed
#from .aes_encrypt import *
import aes_encrypt
import subprocess
import queue
import math
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

def merge(files, save_name):
    '''
    files:  output/*.ts
    '''
    file_num = 0
    with open(save_name,'wb') as fn:
        for ts in natsorted(iglob(files)):
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
    return file_num

#@dataclass
class DownLoad_M3U8(object):
    #m3u8_url  : str
    #file_name : str
    
    def __init__(self, m3u8_url, file_name = ""):
        self.m3u8_url = m3u8_url
        self.file_name = file_name
        self.headers   = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
                          'accept-encoding': 'gzip, deflate, br',
                          #'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
                          }
        self.max_workers = 15
        if not self.file_name:
            self.file_name = 'm3u8new.ts'
        self.base_url = None
        self.key = None
        self.iv = None  
        self.key_uri = None
        self.save_path = "output/%s-d/"%(self.file_name)
        self.total_segments = 0
        self.failed_count = 0
        self.success_count = 0
        self.timeout = 4
        self.max_time = 0
        self.min_time = 1000
        self.sum_time = 0
        self.download_count = 0
        # self.progress_queue = queue.Queue()
        
        try:
            os.makedirs(self.save_path)
        except FileExistsError :
            pass
        except:
            raise

    def update_time(self, tim):
        if(tim > self.max_time):
            self.max_time = tim
        if(tim < self.min_time):
            self.min_time = tim
        self.sum_time += tim
        self.download_count += 1
        
    def get_key(self, seg):
        key = None
        key_uri_src = None
        if ("key" in seg.keys()):
            key_uri_src = seg["key"]["uri"]
            if (key_uri_src == self.key_uri):
                key = self.key
                return key, key_uri_src
            print ("debug: get key from %s" % key_uri_src)
            if (os.path.isfile(self.base_uri)):
                if(not os.path.isabs(key_uri_src)):
                    key_uri = self.base_uri + key_uri_src
                else:
                    key_uri = key_uri_src
                with open(key_uri, 'rb') as fp:
                    key = fp.read()
            else:           
                key_uri = urljoin(self.base_uri, key_uri_src)
                
                try:
                    res = requests.get(key_uri,
                                       headers=self.headers, timeout=3)
                    #print ("get first key :%s"%res.content)
                except Exception as e:
                    print ("[get_first_key:125]get key error: url=%s, %s, get_key" % (
                        key_uri, e))
                    
                    return key, key_uri_src

            if (len(res.content) > 100):
                print ("key len > 100,")
                return key, key_uri_src
            key = res.content
            
        return key, key_uri_src
            
    def get_first_key(self, seg):
        key, key_uri = None, None
        for i in range(3):
            key, key_uri = self.get_key(seg)
            if (not key_uri):
                break
            if (key_uri and key):
                break

        if (key_uri and key):
            self.key = key
            self.key_uri = key_uri
        
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
        t_start = time.time()
        fail = False
        try:
            seg,ts_name = ts_info

            # download key
            key, key_uri = self.get_key(seg)
            if (key_uri and not key):
                print ("get key error: url=%s, %s, get_key %s" %
                       (key_uri, e, ts_name))
                return 1

            #download ts
            url = urljoin(self.base_uri,seg["uri"])
            res = requests.get(url, headers=self.headers,
                               timeout=self.timeout)
            with open(ts_name,'wb') as fp:
                fp.write(res.content)
            
            # decrypt
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
                fail = True
        except requests.exceptions.ReadTimeout as e:
            # print ("\ndownload_single_ts2 download %s ReadTimeout :%s" %(ts_name, e))
            fail = True
        except requests.exceptions.ConnectionError as e:
            # print ("\ndownload_single_ts2 download %s ConnectionError :%s" %(ts_name, e))
            fail = True
            time.sleep(0.5)
        except Exception as e:
            print ("  download_single_ts2 download %s error:%s"%(ts_name,e))
            print ("class name=%s"%(e.__class__.__name__))
            time.sleep(0.5)
            fail = True

        # print("\n ==4== %s use %f" % (ts_name, time.time() - t_start))
        self.update_time(time.time() - t_start)
        if (fail):
            return 1
        return 0
    
    def print_progress(self, count):
        n1 = int(count*50/self.total_segments)
        n2 = 50-n1
        f_perc = 0
        if (count > 0):
            f_perc = self.failed_count*100/count
        print ("\r├%s%s┤ %.2f%%  FAILED:%d(%.2f%%)"%("#"*n1, " "*n2, (count)*100/self.total_segments, self.failed_count, f_perc), end='')
    
    def dump_info(self):
        content = {}
        content["url"] = self.m3u8_url
        content["segments"] = self.total_segments
        content["base_uri"] = self.base_uri
        content["timeout"] = self.timeout
        if(self.key):
            content["key"] = self.key.hex()
            content["key_uri"] = self.key_uri
        else:
            content["key"] = ""
            content["key_uri"] = ""
        
        with open("%s/infomation.txt"%self.save_path, "wb") as f:
            f.write(json.dumps(content).encode())
    
    def load_info(self):
        try:
            with open("%s/infomation.txt"%self.save_path, "rb") as f:
                content = json.load(f)
            self.total_segments = content["segments"]
            self.base_uri = content["base_uri"]
            self.key = bytes.fromhex(content["key"])
            self.key_uri = content["key_uri"]
            try:
                self.timeout = content["timeout"]
            except:
                pass
        except Exception as e:
            content = {}
            # print (e)
            # logging.exception(e)
        return content
            
    def download_all_ts(self):
        res = self.load_info()
        if res:
            print("read info from %s"%(self.save_path))
            m3u8_obj = m3u8.load("%s/tmp.m3u8"%self.save_path)
            # print (res)
        else:
            for i in range(0, 6):
                self.timeout = 4 * math.pow(2, i)
                try:
                    m3u8_obj = m3u8.load(self.m3u8_url,
                                         timeout=self.timeout, headers=self.headers)
                    m3u8_obj.dump("%s/tmp.m3u8"%self.save_path)
                except Exception as e:
                    print ("get m3u8 info error: %s"%e)
                    if (i >= 5):
                        logging.exception("get m3u8 info error")
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
            if (self.key_uri and not self.key):
                return []
            
            #save base_url and key
            self.dump_info()

        if (self.timeout > 30):
            self.max_workers = 20
        elif(self.timeout > 10):
            self.max_workers = 8
        print(f"set timeout:{self.timeout}, maxworker:{self.max_workers}")
        threadpool = ThreadPoolExecutor(max_workers=self.max_workers)
        fail_count = 0
        for i in range(0, 5):
            _count = 0

            ts_segs = self.get_ts_segment(m3u8_obj)
            self.failed_count = 0
            fail_count = 0
            f_set = set()
            for index,ts_seg in enumerate(ts_segs):
                save_name = "%s/%d.ts"%(self.save_path, index)
                if (os.path.exists(save_name)):
                    _count += 1
                    continue
                while (threadpool._work_queue.qsize() > 0):
                    for future in as_completed(f_set):
                        data = future.result()
                        if(data != 0):
                            fail_count += 1
                        f_set.remove(future)
                        _count += 1
                        break

                f = threadpool.submit(self.download_single_ts2, [
                    ts_seg, save_name])
                f_set.add(f)

                self.failed_count = fail_count
                self.print_progress(_count)
                #print ("add %d, qsize=%d\n"%(tmp_count, self.threadpool._work_queue.qsize()))

            # print ("f_set len:%d" % len(f_set))
            # while(_count < self.total_segments):
            for future in as_completed(f_set):
                data = future.result()
                # print(f"main: {data}")
                if(data != 0):
                    fail_count += 1                
                _count += 1
                self.failed_count = fail_count
                self.print_progress(_count)                

            print ("")
            print ("debug: all-%d,done-%d, fail:%d" %
                   (self.total_segments, _count, fail_count))
            if (fail_count == 0):
                break
            print("Failed to download %d segment(s), try again!" %
                  (fail_count))
            
        threadpool.shutdown()
        
        if (fail_count > 0):
            print ("Failed to download some segments, %d" % (fail_count))

    def run(self):
        t_start = time.time()
        print ("downloading...")
        save_name = "output/%s.mp4"%(self.file_name)
        self.download_all_ts()
        if (os.path.exists(save_name)):
            print ('output-%s.mp4 is exists, pass'%(self.file_name))
            return
        
        print ("merging...")
        ts_path = '%s/*.ts' % self.save_path
        file_num = merge(ts_path, save_name)

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