from ar_img_exif_utils import *
import sys



if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print("Error!!")
        print("Usage: img-long-lat.py <img-file-name>")
        
    tags = readGpsExif(sys.argv[1])
        
    gpslong, gpslat = getGpsLongLat(tags)
    longitude, latitude = convertGPStoDegLongLat(gpslong, gpslat)
        
    print("longitude: ",longitude,"latitude: ",latitude)