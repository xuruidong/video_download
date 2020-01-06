# -*- coding: utf-8 -*-

import sys

sys.path.append("./m3u8_download")

import grpc
import mdownload_pb2
import mdownload_pb2_grpc

def get_file_from_url(link, file_name, host="localhost", port=6801):
    conn = grpc.insecure_channel("%s:%d"%(host, port))
    client = mdownload_pb2_grpc.mDownloadStub(channel=conn)
    response = client.addUri(mdownload_pb2.requestData(url=link))
    print("received: " + response.msg)
    '''
    jsonrpc = Aria2RPC()
    set_dir = os.path.dirname(__file__)
    options = {"dir": set_dir, "out": file_name, }
    #print ("dir=%s"%set_dir)
    res = jsonrpc.addUri([link], options = options)
    '''