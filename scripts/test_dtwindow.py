
import numpy as num

def absSinTriangle(x,period):
    """
    
    """
    
    return 
    
    
def absCosTriangle(x,period):
    """
    
    """
    

nsize = 1626
window = 100

weight1 = (num.cos(2.0e0*num.pi*num.arange(nsize)/window))**2
weight2 = (num.sin(2.0e0*num.pi*num.arange(nsize)/window))**2
total = weight1+weight2

x = num.arange(nsize)

points = num.arange(0,nsize,num.floor(0.5*window))
points= num.hstack( (points,nsize) )
set1 = []
set2 = []

for i in range(len(points)):
    if i < len(points)-1:
        i1  = max(0,points[i]-window/2)
    else:
        i1 = points[i-2]+window/2
    i2 = min(points[i]+window/2,points[-1])
    #print i1, i2, i 
    
    if i%2 == 0:
        set1.append( (i1,i2,i) )
        #dtfunc1 = num.hstack((dtfunc1,outy))
    else:
        set2.append( (i1,i2,i) )
        #dtfunc2 = num.hstack((dtfunc2,outy))
    
    print '1 ',set1
    print '2 ',set2

print total