#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import grpc
import mdownload_pb2
import mdownload_pb2_grpc

_HOST = 'localhost'
_PORT = '8080'

def run():
    conn = grpc.insecure_channel(_HOST + ':' + _PORT)
    client = mdownload_pb2_grpc.mDownloadStub(channel=conn)
    response = client.addUri(mdownload_pb2.requestData(url='https://cn5.7639616.com/hls/20191103/0fe6ffcf910e11284b5f86831cd81961/1572768245/index.m3u8'))
    print("received: " + response.msg)

if __name__ == '__main__':
    run()

