# -*- coding:utf-8 -*-
import sys
from mitmproxy import ctx
import threading
import time
from queue import Queue
from aria2_download import *
#from m3u8_download import m3u8_download
import m3u8dRPC


log_path="./log"
download_path = "./download/"

#print ("===%s"%dir(m3u8_download))
#m3u8_download.DownLoad_M3U8("http://www.baidu.com", "m3u8_download.mp4")

g_queue = Queue()
g_download_queue = Queue()

def create_path(path):
    try:
        os.mkdir(path)
    except FileExistsError :
        pass
    except:
        raise

def thread_fun():
    log_name = "%s/request-%s.log"%(log_path, time.strftime("%Y%m%d", time.localtime()))
    try:
        request_url_log = open(log_name, "a+")
        request_url_log.write("--------------")
        request_url_log.write("%s\n"%time.strftime("%Y%m%d%H%M%S", time.localtime()))
    except Exception as e:
        print("req log Exception %s"%e)
    
    lasttime = time.time()  
    old_file_list = []
    while True:
        try:
            ret = g_queue.get()
            response = ret.response
            if (response.status_code not in [200, 206]):
                continue
            
            #print ("++++%s"%response.headers.get("content-type"))
            #print (dir(response.headers))
            content_type = response.headers.get("content-type")
            if (content_type):
                t_list = content_type.split("/")
                if (t_list[0] in ["text", "image"]):
                    continue
            #print ("++++++++++++++++++++")
            
            request_url = ret.request.url
            #print(request_url)
            tmp_list = request_url.split("?")
            #if (tmp_list[0].endwith() )
            end = tmp_list[0].split(".")

            if(end[-1] in ["mp4","flv", "f4v", "m3u8"]):
                
                filename = tmp_list[0].split("/")[-1]
                if (filename in old_file_list):
                    continue
                    #pass
                old_file_list.append(filename)
                
                request_url_log.write("[%s]%s\n"%(time.strftime("%Y%m%d%H%M%S", time.localtime()), request_url))
                tmp = {}
                tmp["type"] = end[-1]
                tmp["url"] = request_url
                
                #g_download_queue.put( request_url.split("range=")[0].rstrip("?&") )
                g_download_queue.put(tmp)
                #print ("---================================================thread %s"%request_url)
            if (time.time() - lasttime > 15):
                lasttime = time.time() 
                request_url_log.close()
                request_url_log = open(log_name, "a")
                
        except Exception as e:
            print ("================================\n============except %s"%e)


def thread_download():
    log_name = "%s/download-%s.log"%(log_path, time.strftime("%Y%m%d", time.localtime()))
    try:
        download_log = open(log_name, "a+")
        download_log.write("--------------")
        download_log.write("%s\n"%time.strftime("%Y%m%d%H%M%S", time.localtime()))
    except Exception as e:
        print("download log Exception %s"%e)
        
    while True:
        try:
            ret = g_download_queue.get()
            #print ("down load %s"%ret)
            #download_log.write("%s\n"%time.strftime("%Y%m%d%H%M%S", time.localtime()))
            download_log.write("[%s]%s\n"%(time.strftime("%Y%m%d%H%M%S", time.localtime()), ret))
            download_log.close()
            download_log = open(log_name, "a")
            
            req_url = ret["url"]
            tmp1 = req_url.split("?")[0]
            tmp2 = tmp1.split("/")
            filename = tmp2[-1]
            
            if (ret["type"] == "m3u8"):
                #if ("f30741" not in filename):
                #    continue
                m3u8dRPC.get_file_from_url(req_url, "unused")
                
                print("download m3u8: %s"%req_url)
            else:
                url = ret["url"].split("range=")[0].rstrip("?&")
                get_file_from_url(url, "%s/%s-%s"%(download_path, time.strftime("%Y%m%d%H%M%S", time.localtime()), filename))
        
        except Exception as e:
            print ("================================\n============thread_download----except %s"%e)

create_path(log_path)
create_path(download_path)

thread1 = threading.Thread(target=thread_fun,args=())
thread1.setDaemon(True)
thread1.start()

thread2 = threading.Thread(target=thread_download,args=())
thread2.setDaemon(True)
thread2.start()

# 所有发出的请求数据包都会被这个方法所处理
# 所谓的处理，我们这里只是打印一下一些项；当然可以修改这些项的值直接给这些项赋值即可
def request(flow):
    # 获取请求对象
    #request = flow.request
    # 实例化输出类
    #info = ctx.log.info
    # 打印请求的url
    #info(request.url)
    # 打印请求方法
    #info(request.method)
    # 打印host头
    #info(request.host)
    # 打印请求端口
    #info(str(request.port))
    # 打印所有请求头部
    #info(str(request.headers))
    # 打印cookie头
    #info(str(request.cookies))
    #g_queue.put(request.url)
    pass

# 所有服务器响应的数据包都会被这个方法处理
# 所谓的处理，我们这里只是打印一下一些项
def response(flow):
    '''
    # 获取响应对象
    response = flow.response
    # 实例化输出类
    info = ctx.log.info
    # 打印响应码
    info(str(response.status_code))
    # 打印所有头部
    #info(str(response.headers))
    # 打印cookie头部
    #info(str(response.cookies))
    # 打印响应报文内容
    #info(str(response.text))
    print (dir(response))'''
    #print ("flow=%s"%flow)
    #print (dir(flow))
    
    g_queue.put(flow)
    