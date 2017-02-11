from ar_img_exif_utils import *
import os

mykeys = readProjectKeys()
projects = getProj_Keys_n_Coords(mykeys)

img_dict={}
file_lst= os.listdir()
myindx = createProjectIndex(projects,200)#radius of 200 feet should be wide enough
img_dict,file_lst = mapPicturesToProjects(myindx,file_lst)
myindx.close()

for key in img_dict.keys():
    #create a folder
    try:
        if key not in os.listdir():
            #make dir
            os.mkdir(key)
    except:
        print("Couldn't make directory ",key)
    
    
    for img in img_dict[key]:
        #move the picture to the foder
        try:
            os.rename(img,os.path.join(key,img))
        except:
            print ("Could not copy image ",img)