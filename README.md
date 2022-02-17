# video_download


### Prerequisites

The following dependencies are necessary:

* **[Python](https://www.python.org/downloads/)**  3.7
* **[aria2](https://aria2.github.io/)** 

```
# pip install requests
# pip install pycryptodome

Package      Version
------------ ---------
certifi      2021.10.8
chardet      3.0.4
idna         2.8
iso8601      1.0.2
m3u8         0.3.12
natsort      6.0.0
pip          19.0.3
pycryptodome 3.8.2
requests     2.22.0
setuptools   40.8.0
urllib3      1.25.11
```

## Getting Started

### Download a video with m3u8

如果获取m3u8时总是失败，比如返回404，可以在浏览器中调试模式找到m3u8内容，复制到本地文件。（此时需要注意是否需要修改ts文件的url）

#aria2c.exe  --conf-path=aria2.conf


#mitmdump -s proxy.py --flow-detail 0



