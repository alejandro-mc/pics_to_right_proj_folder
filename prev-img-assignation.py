from ar_img_exif_utils import *


mykeys = readProjectKeys()
projects = getProj_Keys_n_Coords(mykeys)

img_dict={}
file_lst= os.listdir()
myindx = createProjectIndex(projects,200)#radius of 200 feet should be wide enough
img_dict,file_lst = mapPicturesToProjects(myindx,file_lst)
myindx.close()

for key in img_dict.keys():
    print(key,":")
    for img in img_dict[key]:
        print ("\t| ",img)