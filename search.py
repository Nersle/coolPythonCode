#-*- coding:utf-8 -*-	
#	
#   Author :    sec_lee	
#   Time   :    2014-4-10	
#   Function:   You can use it to query items in	
#                twenty million hotel occupancy data	
#   Memo:       1.The next version supports multi-threading <done:2014-4-20>
#               2.If need , we will add a thread pool and solute the speed in
#                   single key words search
#
import re
import time
import _thread

mylock=_thread.allocate_lock()
searchNum=0
dataPage=11

def search(findKey):
    #mylock.acquire()
    #global searchNum
    #searchNum=searchNum+1
    #mylock.release()
    
    print("Key Words:%s"%(findKey))
    output=open("result"+findKey+".txt","w",encoding="utf-8")
    fileNum=dataPage 
    for i in range(fileNum):
        fileName="%d.csv"%(i+1)
        print("search %s in %s\n"%(findKey,fileName))
        handle=open(fileName,"r",encoding="utf-8")
        item=handle.readline()
        while(item):
            #if(re.search(findKey,item)):
            if(item.find(findKey)>-1):
                output.write("file"+str(i)+"  "+item)
                #print(item)
            item=handle.readline()
        handle.close()
def adapter(searchListStr):
    searchList=searchListStr.split("#")
    #print("we get list:")
    #print(searchList) 
    for key in searchList:
        search(key) 
    _thread.exit_thread()

def multiplyThread(threadNum,searchList):
    keyLen=len(searchList)
    start=0
    end=0
    step=keyLen/threadNum
    #print(keyLen)
    temp=()
    for i in range(threadNum):
        end=int(start+step)
        if(end>keyLen):
            end=keyLen
        temp=searchList[int(start):end] 
        strs="#".join(temp) 
        temp=(strs,) 
        start=int(end)
        #print(temp)
        _thread.start_new_thread(adapter,temp)
    if end<keyLen:
        end=int(start+step)
        if(end>keyLen):
            end=keyLen
        temp=searchList[int(start):end] 
        strs="#".join(temp) 
        temp=(strs,) 
        start=int(end)
        #print(temp)
        _thread.start_new_thread(adapter,temp)       

if __name__=="__main__":
    #findKey=input("---input the key----\n")
    inputFile=open("key.txt","r",encoding="utf-8")
    itemKey=inputFile.readline()
    searchKeys=[]
    while itemKey:
        #search(itemKey[:-1])
        searchKeys.append(itemKey[:-1])
        itemKey=inputFile.readline()
    print(searchKeys)
    multiplyThread(2,searchKeys)
    #print("we search %d keys"%(searchNum))
        
