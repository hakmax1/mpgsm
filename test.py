
import _thread
import time
#

def testThread():
    i = 0
    while i<10:
        i=i+1
        print("Hello from thread")
        time.sleep(1)
        
        
def testThread(arg):
i = 0
while i<10:
i=i+1
print("Hello from thread")
time.sleep(1)

def test():
i = 0
while i<10:
i=i+1
print("Hello from thread")
print(_thread.getSelfName())
mainID = _thread.getReplID()
print(mainID)
print(_thread.getmsg())
print(_thread.wait())

while _thread.wait() :
#_thread.sendmsg(mainID, i)


time.sleep(2)


thrID = _thread.start_new_thread("test",test,())
_thread.sendmsg(thrID, 5)
_thread.getmsg()
_thread.list()
_thread.notify(thrID, 1)




#k=_thread.start_new_thread("testThr",testThread,(1,))


_thread.start_new_thread(testThread())

k=0
while k<15:
    k=k+1
    time.sleep(1)
    print("Hello from main")
    pass