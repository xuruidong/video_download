# -*- coding: utf-8 -*-
import m3u8
import requests


class choose_m3u8(object):
    def __init__(self, m3u8_url):
        self.m3u8_url = m3u8_url
        pass
    
    
    def m3u8_parse(self):
        m3u8_obj = m3u8.load(self.m3u8_url)
        #self.base_uri = m3u8_obj.base_uri
        print (m3u8_obj.keys)
        print (m3u8_obj.segments)
        print (m3u8_obj.data)   
        playlist = m3u8_obj.data["playlists"]
        for play_elem in m3u8_obj.data["playlists"]:
            stream_info = play_elem["stream_info"]
            resolution = stream_info["resolution"]
            url = play_elem["uri"]
            program_id = stream_info["program_id"]
            print ("%s:"%program_id)
            print (url)
            print (resolution)
            
            

if __name__ == "__main__":
    
    url = "https://1258712167.vod2.myqcloud.com/fb8e6c92vodtranscq1258712167/e63bb0965285890793191478353/drm/voddrm.token.dWluPTk4Njg3MjU4Mzt2b2RfdHlwZT0wO2NpZD0yNDQ5Mzg7dGVybV9pZD0xMDA1MDg1NjE7cGxza2V5PTAwMDQwMDAwNGRkMDIyMTBkMWYzOWFlNWM3NmRhYjAxNDc3MjQwNDNiODFhODAyNmY0OWY2MDRmOTQzNzVjZDIyNmY1ZWUxODQ5MGIwNWMzYjljM2E3N2U7cHNrZXk9.master_playlist.m3u8?t=5d882e8a&exper=0&us=8937642039305098998&sign=fe07d0fc94b9617148f2fd124332d09c"
    playlist = choose_m3u8(url)
    playlist.m3u8_parse()
    print ("end")