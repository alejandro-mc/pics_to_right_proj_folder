import exifread
import os
import datetime
from rtree import index
import pyproj
import csv


#converGPStoNYLISP
#converts GPS DMS coordinates to coordinates
#in the New York - Long Island State Plane Projection Coordinates
def convertGPStoNYLISPC (GPSLong,GPSLat):
    Degs,Mins,Secs = (0,1,2)
    Long = []
    Lat=[]
    #data Degs Mins and Secs are Ratios
    #convert them to floats
    Lat.append(float(GPSLat[Degs].num))
    Lat.append(float(GPSLat[Mins].num))
    Lat.append(float(GPSLat[Secs].num / GPSLat[Secs].den))
    
    Long.append(float(GPSLong[Degs].num))
    Long.append(float(GPSLong[Mins].num))
    Long.append(float(GPSLong[Secs].num / GPSLong[Secs].den))
    
    degLat  = Lat[Degs] + (60*Lat[Mins] + Lat[Secs]) / (60*60)
    degLong = Long[Degs] + (60*Long[Mins] + Long[Secs]) / (60*60)
    
    #convert to New York - Long Island State Plane Cordinates (ESRI:102718)
    projectstr = "+proj=lcc +lat_1=40.66666666666666 +lat_2=41.03333333333333 +lat_0=40.16666666666666 +lon_0=-74 +x_0=300000 +y_0=0 +ellps=GRS80 +datum=NAD83 +to_meter=0.3048006096012192 +no_defs"
    p = pyproj.Proj(projectstr,preserve_units=True)
    
    xcoord,ycoord = p(-degLong,degLat)  
    return (xcoord,ycoord)

#PRE: GPSLong, GPSLat: are strings of the form [degrees,minutes,seconds] with seconds expresed as a fraction
def convertGPStoDegLongLat(GPSLong,GPSLat):
    Degs,Mins,Secs = (0,1,2)
    Long = []
    Lat=[]
    #data Degs Mins and Secs are Ratios
    #convert them to floats
    Lat.append(float(GPSLat[Degs].num))
    Lat.append(float(GPSLat[Mins].num))
    Lat.append(float(GPSLat[Secs].num / GPSLat[Secs].den))
    
    Long.append(float(GPSLong[Degs].num))
    Long.append(float(GPSLong[Mins].num))
    Long.append(float(GPSLong[Secs].num / GPSLong[Secs].den))
    
    degLat  = Lat[Degs] + (60*Lat[Mins] + Lat[Secs]) / (60*60)
    degLong = Long[Degs] + (60*Long[Mins] + Long[Secs]) / (60*60)
    
    return degLong,degLat


#create rtree index for project list
#PRE: keys_coords is a list of ((Borough,Block,Lot),(xcoord,ycoord)) pairs
#     Borough, Block and Lot are strings
#     xcoord and ycoord are integers
#     radius: is the radius around the project location where an image is assumed to be part of
#             a given project

#Post: Returns an rtree index for elements in keys_coords
#

def createProjectIndex(keys_coords,radius=10):
    
    proj_index = index.Rtree()
    
    idx=0
    for key_coord in keys_coords:
        
        key = key_coord[0]
        xcoord,ycoord = key_coord[1]
        
        #find bounding box around lot
        left,right = xcoord - radius, xcoord + radius 
        bottom,top = ycoord - radius, ycoord + radius
        
        #insert key in the rtree index
        #print("inserting idx=" + str(idx) + " left= " + str(left) + " bottom = " + str(bottom) +" right= " + str(right) + "top= " + str(top))
        proj_index.insert(idx,(left,bottom,right,top),obj=(key,(xcoord,ycoord)))
        
        idx+=1
    
    return proj_index
    

#PRE:  project_keys is a list of the form [(Borough_1,Block_1,Lot_1),....(Borough_n,Block_n,Lot_n)]
#POST: keys_coords is a list of ((Borough,Block,Lot),(xcoord,ycoord)) pairs
def getProj_Keys_n_Coords(project_keys):
    plutofiles = ['BK.csv',  'BX.csv',  'MN.csv',  'QN.csv',  'SI.csv']
    
    keys_coords = []
    idx =0
    for file in plutofiles:
        with open(file,'r') as borough_file:
            borough_reader = csv.DictReader(borough_file)
            for lot in borough_reader:
                key = (lot['Borough'],lot['Block'],lot['Lot'])
                if key in project_keys:
                    #get lot coordinates
                    xcoord = int(lot['XCoord'])
                    ycoord = int(lot['YCoord'])
                    
                    #add project keys and coordinates
                    keys_coords.append((key,(xcoord,ycoord)))
                    
                    #remove index from the list
                    project_keys.remove(key)
                    if len(project_keys) == 0:
                        return keys_coords
                    
                    #increment index
                    idx+=1
                    
    #WARNING if this stage is reached there must a wrong entry
    #in the project key or the pluto file, let the user know
    print("the following projects were not found:")
    for pr in project_keys:
        print(pr)
        
    return keys_coords

#PRE: proj_index is an rtree index whose entries have obj = (project_key,(project_xcoord,project_ycoord))
#     file_list  is the list of file names as strings
#     imgDict    is dictionary where keys are the project_key and values are the list of image names that belong to that project
#                defaults to 0

#POST image file names have been added to the lists in imgDict corresponding to 
#     the projects they are closest geographically  
def mapPicturesToProjects(proj_index,file_list,imgDict = {}):
    
    for image in file_list:
        try:
            #try extrating the exif info
            with open(image,'rb') as f:
                #read the exif tags
                tags = exifread.process_file(f)
                xcoord,ycoord = convertGPStoNYLISPC (tags['GPS GPSLongitude'].values,\
                                                    tags['GPS GPSLatitude'].values)
                
                #filterout pictures that are too far
                if xcoord < 905245 or xcoord > 1057756 or\
                   ycoord < 120018 or ycoord > 287281:
                        #put in the too far category
                        directory = "outside_nyc"
                        imgDict[directory] = imgDict.get(directory,[]) + [image]
                        file_list.remove(image)
                        continue
                
                #find collitions
                intersections = [lot.object for lot in proj_index.intersection((xcoord,ycoord,xcoord,ycoord),objects=True)]
                if len(intersections) != 1:
                    if len(intersections) > 1:
                        #if multiple candidates put it in the folder of the colsest property
                        mindist=1000000000000000000000000
                        minkey=0
                        for obj in intersections:
                            #compute distance between img location and project location 
                            #obj[1] is (lot xcoord,lot ycoord)
                            dist = distSqrd((xcoord,ycoord),obj[1])
                            if  dist < mindist:
                                mindist = dist
                                minkey = obj[0]
                    
                        #move to special folder for images that must be moved manually
                        #os.rename(image,os.path.join('insert_manually',image))
                        directory = minkey[0] + "_" +\
                                    minkey[1] + "_" +\
                                    minkey[2]
                    
                        #make directory to move the images
                        #if not os.path.exists(directory):
                        #       os.mkdir(directory)
                        #put image in image dictionary
                        imgDict[directory] = imgDict.get(directory,[]) + [image]
                        file_list.remove(image)
                    
                    else:
                        pass
                        #print("could not find xcoord: " + str(xcoord) + " ycoord: " + str(ycoord))

                else:
                    #intersections is a list [((Borough,Block,Lot),(xcoord,ycoord)),.....]
                    directory = intersections[0][0][0] + "_" +\
                                intersections[0][0][1] + "_" +\
                                intersections[0][0][2]
                    #put image in the dictionary
                    imgDict[directory] = imgDict.get(directory,[]) + [image]
                    file_list.remove(image)
                    
        except Exception as e:
            print(e)
            print("EXIF could not be extracted from " + image)
            file_list.remove(image)
            
    
    return imgDict, file_list

#PRE:  p1 and p2 are tuples representing points
#POST: computes the euclidian distance squared between p1 and p2
def distSqrd(p1,p2):
    return sum([(i[0]-i[1])**2 for i in zip(p1,p2)])



#read projcets from file
#PRE: there is a csv file named proj_file in the current working directory
#proj_file must have the following required fields: Borough, Block, Lot

#POST: keys is a list of the form [(Borough_1,Block_1,Lot_1),....(Borough_n,Block_n,Lot_n)]
def readProjectKeys():
    keys = []
    with open('proj_file','r') as proj_file:
        reader = csv.DictReader(proj_file)
        for project in reader:
            #create keys
            key = (project['Borough'],project['Block'],project['Lot'])
            keys.append(key)
    
    return keys


def readGpsExif(img_filename):
    try:
        print("Trying to read EXIF from ",img_filename)
        with open(img_filename,'rb') as f:
            tags = exifread.process_file(f)
    except:
        print("Could not read EXIF info")
        return -1
    
    return tags

#PRE tags is a dictionary containing exif data, must have fields
#         'GPS GPSLongitude' and 'GPS GPSLatitude'
def getGpsLongLat(tags):
    return tags['GPS GPSLongitude'].values, tags['GPS GPSLatitude'].values


#PRE:  img-filename is the name of an image file
#POST: prints the eix info for an image
def printGpsExif(img_filename):
    
    tags = readGpsExif(img_filename)
    
    for gps_tag in filter(lambda s: "GPS" in s.upper(),tags.keys()):
        print(gps_tag,": ",tags[gps_tag])
