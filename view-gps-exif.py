from ar_img_exif_utils import *
import sys



if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("Error!!")
        print("Usage: view-exif.py <img-file-name>")
    
    printGpsExif(sys.argv[1])
    