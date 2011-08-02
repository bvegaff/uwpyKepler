import sys
import MySQLdb
import numpy as num
import scipy
import pylab
import uwpyKepler as kep
#num.warning.warn(action = 'ignore')
import warnings
warnings.simplefilter('ignore', num.RankWarning)
from uwpyKepler.io import ApplyMask
 
def detrendData(data, window, polyorder):
    """Detrends the data"""
    
    dout = {}
    # loop through portions
    
    for portion in data.keys():
        
	data = ApplyMask(data,'OTMask')
        print ' yo ', num.ma.count_masked(data[portion]['x']), num.shape(num.where(data[portion]['OTMask']))
        
        nsize = len(data[portion]['x'])
        points = num.arange(0,nsize,0.5*window)
        points= num.hstack( (points,nsize))
        dtfunc1 = num.array([])
        dtfunc2 = num.array([])
        set1 = []
        set2 = []
        weight1 = (num.cos(2.0e0*num.pi*num.arange(nsize)/window))**2
        weight2 = (num.sin(2.0e0*num.pi*num.arange(nsize)/window))**2
        
        for i in range(len(points)):
            if i < len(points)-1:
                i1  = long(max(0,points[i]-window/2))
            else:
                i1 = long(points[i-2]+window/2)
            i2 = long(min(points[i]+window/2,points[-1]))
            
            b = num.where(data[portion]['x'][i1:i2].mask == False)[0].tolist()
            xdata = num.array(data[portion]['x'][i1:i2][b])
            ydata = num.array(data[portion]['y'][i1:i2][b])
            print b[-1], len(b), num.shape(xdata), num.ma.count_masked(data[portion]['x'][i1:i2])
            print num.where(data[portion]['y'][i1:i2].mask)[0].tolist()
            
            # find the fit
            pylab.plot(xdata,ydata,'ro')
            coeff = scipy.polyfit(xdata, ydata, polyorder)

            # unmask data and apply the polynomial
            data[portion]['x'][i1:i2].mask = data[portion]['UnMasked'][i1:i2]
            data[portion]['y'][i1:i2].mask = data[portion]['UnMasked'][i1:i2]
            data[portion]['yerr'][i1:i2].mask = data[portion]['UnMasked'][i1:i2]
            
            #print num.ma.count_masked(xdata), num.ma.count_masked(ydata), num.ma.count_masked(data[portion]['x'][i1:i2])
            outy = scipy.polyval(coeff,data[portion]['x'][i1:i2])
            pylab.plot(data[portion]['x'][i1:i2],data[portion]['x'][i1:i2],'b.')

            if i%2 == 0:
                set1.append( (i1,i2) )
                dtfunc1 = num.hstack((dtfunc1,outy))
                pylab.plot(data[portion]['x'][i1:i2],outy,'y-',linewidth=3)
            else:
                set2.append( (i1,i2) )
                dtfunc2 = num.hstack((dtfunc2,outy))
                pylab.plot(data[portion]['x'][i1:i2],outy,'c-',linewidth=3)
            
        #print set1
        #print set2
        #print len(data[portion]['x']), len(dtfunc1), len(dtfunc2), len(outy)
            
        mergedy = weight1*dtfunc1 + weight2*dtfunc2

        # apply correction
        newarr = data[portion]['y']/mergedy
        newerr = data[portion]['yerr']/mergedy
        #pylab.plot(data[portion]['x'],data[portion]['y'],'b.')
        #pylab.plot(data[portion]['x'],mergedy,'k-',linewidth=3)
        #pylab.plot(data[portion]['x'],dtfunc1,'y-',linewidth=3)
        #pylab.plot(data[portion]['x'],dtfunc2,'c-',linewidth=3)
        
        data = ApplyMask(data,'UnMasked')
        dout[portion] = {'x':data[portion]['x'],'y':newarr,'yerr':newerr,'TransitMask':data[portion]['TransitMask'],'OTMask':data[portion]['OTMask'],'OutlierMask':data[portion]['OutlierMask'],'UnMasked':data[portion]['UnMasked'],'Correction':mergedy}
    pylab.show()    
    return dout

def cutOutliers(data):
    """ This function cuts out outliers. 
        Inputs - data = data dictionary
               - medwin = the window size used to compute the median
               - threshold = the sigma-clipping factor (suggested, 3 or greater)
        Outputs - the x data now only contains times that don't correspond to outliers. 
    """

    # tagging outliers
    idx=num.where(data['OutlierMask']==False)
    
    print len(data['x']), len(data['OutlierMask']), len(data['TransitMask']),len(data['UnMasked']), len(data['OTMask'])
    
    xnew = []
    ynew = []
    yerrnew = []

    for el in idx:
        xnew.append(data['x'][el])
        ynew.append(data['y'][el])
        yerrnew.append(data['yerr'][el])

    print num.shape(num.array(xnew).ravel())
    
    dout= {'kid':data['kid'],'x':num.array(xnew).ravel(),'y':num.array(ynew).ravel(),'yerr':num.array(yerrnew).ravel()}
        
    return dout

def cutTransits(dTransit):
    	""" This function cuts out points within a tranit.
         
         Input = data dictionary
         Output = data dictionary without points in transits.
        """
    	
	xnew = []
	ynew = []
	yerrnew = []
	
	idx=num.where(dTransit['TransitMask'] == False)
        for element in idx:
		xnew.append(dTransit['x'][element])
		ynew.append(dTransit['y'][element])
		yerrnew.append(dTransit['yerr'][element])
		
		
	dout= {'kid':dTransit['kid'],'x':num.array(xnew),'y':num.array(ynew),'yerr':num.array(yerrnew)}

        return dout


def cutOT(data):
    d2=kep.proc.cutTransits(data)
    d3=kep.proc.cutOutliers(d2,10,4)
    return d3

def stackPortions(data):
    """rejoins/stacks all portions in the dictionary into one."""
    xarr=num.array([])
    yarr=num.array([])
    yerrarr=num.array([])
    TransitMask=num.array([])
    OutlierMask=num.array([])
    OTMask=num.array([])
    UnMasked=num.array([])
    
    
    for portion in data.keys():
        xarr=num.hstack((xarr,data[portion]['x']))
        yarr=num.hstack((yarr,data[portion]['y']))
        yerrarr=num.hstack((yerrarr,data[portion]['yerr']))
        print type(data[portion]['TransitMask'])
        TransitMask=num.hstack((TransitMask,data[portion]['TransitMask']))
        OutlierMask=num.hstack((OutlierMask,data[portion]['OutlierMask']))
        OTMask=num.hstack((OTMask,data[portion]['OTMask']))
        UnMasked=num.hstack((UnMasked,data[portion]['UnMasked']))
        
        #print len(data[portion]['x']), len(xarr), portion
    kid=data[portion]['kid']
    
    
    pd={'OTMask':OTMask,'TransitMask':TransitMask,'OutlierMask':OutlierMask,'UnMasked':UnMasked,'yerr':yerrarr,'y':yarr,'x':xarr,'kid':kid}
    return pd