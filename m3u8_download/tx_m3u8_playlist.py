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
            print ("%s%s"%(m3u8_obj.base_uri, url))
            print (resolution)
            
            

if __name__ == "__main__":
    
    url = "https://"
    playlist = choose_m3u8(url)
    playlist.m3u8_parse()
    print ("end")