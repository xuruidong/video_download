
import sys
from natsort import natsorted
from glob import iglob

def combine_ts(path, file_name):
    ts_path = '%s/*.ts'%path
    with open(file_name,'wb') as fn:
        for ts in natsorted(iglob(ts_path)):
            print (ts)
            with open(ts,'rb') as ft:
                scline = ft.read()
                fn.write(scline)

if __name__ == "__main__":
    path = "./"
    filename = "new.mp4"
    try:
        path = sys.argv[1]
        filename = sys.argv[2]
    except:
        pass
    print ("path=%s"%path)
    print ("filename=%s"%filename)
    
    combine_ts(path, filename)
    print ("end")