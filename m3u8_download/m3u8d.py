#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import grpc
import time
from concurrent import futures
import queue
import threading
import signal

import mdownload_pb2
import mdownload_pb2_grpc
import m3u8_download

def handler(sig, frame):
    print('Got signal: ', sig)
    
class mDownload(mdownload_pb2_grpc.mDownloadServicer):
    def __init__(self):
        self.task_queue = queue.Queue()
        self.uri_list = []
        
        self.downthread = threading.Thread(target= self.thread_handle)
        self.downthread.setDaemon(True)
        self.downthread.start()
        
    
    def thread_handle(self):
        while True:
            try:
                task = self.task_queue.get()
                uri_str = task["uri"]
                
                M3U8 = m3u8_download.DownLoad_M3U8(uri_str,"new.ts")
                M3U8.run() 
                
                
            except Exception as e:
                print ("thread_handle error: %s"%e)
        
    
    def addUri(self, request, context):
        retMsg = ""
        try:
            urlstr = request.url
            tmp = {}
            tmp["uri"] = request.url
            self.task_queue.put(tmp)   
        except Exception as e:
            retMsg = "%s"%e
        return mdownload_pb2.responseData(msg=retMsg)

def serve(host, port):
    grpcServer = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    mdownload_pb2_grpc.add_mDownloadServicer_to_server(mDownload(), grpcServer)
    grpcServer.add_insecure_port("%s:%d"%(host, port))
    grpcServer.start()
    print("listen on %s:%d"%(host, port))
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        grpcServer.stop(0)

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, handler)
    serve('localhost', 6801)