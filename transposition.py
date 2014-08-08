#-*- coding:utf-8 -*-
#
#   Author :    sec_lee
#   Time   :    2014-4-18
#   Function:   You can use it to  crack transposition cryptography
#   Memo:       The next version supports multi-threading 
#
def statis(keyFile):
    file=open(keyFile,"r")
    content=file.readlines()
    print(content[0])
    ary=[]
    for i in range(26):
        ary.append(0) 
    print(ary)
    strs=content[0]
    strs=strs.lower()
    print(strs)
    strlen=len(strs)
    start=ord('a')-1
    end=ord('z')+1
    sums=0
    for i in range(strlen): 
        n=ord(strs[i]) 
        if n<end and n> start:
            ary[n-ord('a')]=ary[n-ord('a')]+1
            sums=sums+1
    print(sums)
    print(ary)
    s=len(ary) 
    det=[]
    for i in range(s):
        det.append(ary[i]/sums*100)
    print(det)
    for i in range(26):
        print(det[i])
def change2word(string):
    strlen=len(string)
    reStr=""
    i=0
    while i<strlen: 
            reStr=reStr+string[i+1]+string[i]
            i=i+2
    return reStr
            
            
        
if __name__=="__main__":
    #statis("key.txt")
    strs="xxx"
    print(change2word(strs))
