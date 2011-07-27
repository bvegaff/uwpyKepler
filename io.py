import MySQLdb
import sys
import numpy as num
import scipy
    
def ReadLightCurve(KeplerID):
    """ This function reads the Kepler database and returns the 
    corrected lightcurve in a dictionary
    
    Input = KeplerID
    Output = Dictionary with time, flux and fluxerror data
    """

    db     = MySQLdb.connect(host='tddb.astro.washington.edu', user='tddb', passwd='tddb', db='Kepler')
    cursor = db.cursor()
    foo    = 'select * from source where (KEPLERID = %s)' % (KeplerID)
    cursor.execute(foo)
    results = cursor.fetchall()
    
    # reading time, corrected flux and flux errors
    time    = num.ma.array([x[2] for x in results])
    corflux = num.ma.array([x[7] for x in results])
    corerr  = num.ma.array([x[8] for x in results])
    
    if len(time) == 0:
        print 'No data found for KID  %s' % (KeplerID)
        sys.exit(1)
    
    idx = num.where((corflux>0)&(corerr>0))
    
    time    = time[idx]
    corflux = corflux[idx]
    corerr  = corerr[idx]
    
    return {'kid':KeplerID,'x':time,'y':corflux,'yerr':corerr}

def db(pd):
    """queries the database for various stuff"""
    period = []
    epoch = []
    duration = []
    db     = MySQLdb.connect(host='tddb.astro.washington.edu', user='tddb', passwd='tddb', db='Kepler')
    cursor = db.cursor()
    foo1 = 'select Period, Dur, Epoch from KEPPC where (KID = %s)' % (pd['kid'])
    cursor.execute(foo1)
    results = cursor.fetchall()
    if len(results) == 0:
	    foo1 = 'select Period, Duration, Epoch from KEPFP where (KID = %s)' % (pd['kid'])
	    cursor.execute(foo1)
	    results = cursor.fetchall()
    	    if len(results) == 0:
		    results = ()
    print len(results)
    return results
   
    

def FlagTransits(pd,results):
    	""" This function flags points within a tranit and
        applies a mask.
         
         Input = data dictionary
         Output = data dictionary with addition of the keys
         'TransitMask' and 'UnMasked'
        """
        mask0=num.ma.getmaskarray(pd['x'])
	pd['UnMasked']=mask0
	for i in range(len(results)):
		period = results[i][0]
		t0 = results[i][2]
		dur = results[i][1]
		dur = (1.2*dur/24e0)
		t0 = t0 + 54900e0
        # defining start and end time lists
		width = dur/period
		maxphase=1-width/2
		minphase=width/2
		phase= (pd['x']-t0)/period-(pd['x']-t0)//period
		idx=num.where((phase>maxphase)|(phase<minphase))
		pd['x'][idx]= num.ma.masked
		mask1=num.ma.copy(pd['x'].mask)
		if i == 0:
			pd['TransitMask']=mask1
		else:
			pd['TransitMask']=num.ma.mask_or(mask1,pd['TransitMask'])

        return pd

def SplitGap(data,gapsize):
	"""
        This function finds gaps and splits data into portions.
        
        Input =  data - data dictionary
                 gapsize - size of gap in days
               
        Output = new data dictionary with data split into portions
	"""
	
	# defining new empty lists and stuff
	pcount=0
        istamps=[]
	pd={}
	
	# minimum sized gap that we are flagging, 2.4 hours
	# The grand master loop >=}
        # to make portion slices
	for i in range(len(data['x'])-1):
		dt =  data['x'][i+1]- data['x'][i]
                if pcount == 0:
                    i0 = 0
                if pcount > 0:
                    i0 = i1+1
		if dt > gapsize:
                    i1 = i
                    istamps.append([i0,i1])
                    pcount += 1
        i1 = i+1
        istamps.append([i0,i1])
        # Applying slices
        for j in range(len(istamps)):
            pd['portion' + str(j+1)] = {'kid':data['kid'],'x':data['x'][istamps[j][0]:istamps[j][1]+1], 'y':data['y'][istamps[j][0]:istamps[j][1]+1], 'yerr':data['yerr'][istamps[j][0]:istamps[j][1]+1], 'TransitMask':data['TransitMask'][istamps[j][0]:istamps[j][1]+1],'UnMasked':data['UnMasked'][istamps[j][0]:istamps[j][1]+1]}
             
        return pd
                
def FlagOutliers(data,medwin,threshold):
    """ This function flags outliers. 
        Inputs - data = data dictionary
               - medwin = the window size used to compute the median
               - threshold = the sigma-clipping factor (suggested, 3 or greater)
        Outputs - the data dictionary now contains mask arrays named
                'OutlierMask' and 'BothMask'
    """
    
    dout = {}
    # cycling through portions
    for portion in data.keys():
        data[portion]['x'].mask = data[portion]['TransitMask']
        data[portion]['y'].mask = data[portion]['TransitMask']
        data[portion]['yerr'].mask = data[portion]['TransitMask']
        npts = len(data[portion]['x'])
        
        # defining the window
        medflux = []
        medhalf = (medwin-1)/2

        # placing the window and computing the median
        for i in range(npts):
            i1 = max(0,i-medhalf)
            i2 = min(npts, i + medhalf)
            medflux.append(num.median(data[portion]['y'][i1:i2]))
        
        # finding outliers
        medflux = num.array(medflux)
        outliers = data[portion]['y'] - medflux
        
        outliers.sort()
        sigma = (outliers[.8415*npts]-outliers[.1585*npts])/2
        outliers = data[portion]['y'] - medflux
        
        # tagging outliers (which are not part of the transit)
        idx=num.where( (abs(num.array(outliers))>threshold*sigma) & (data[portion]['TransitMask'] == False) )

        # creating the outlier mask
        data[portion]['x'].mask = data[portion]['UnMasked']
        data[portion]['x'][idx[0]] = num.ma.masked
        
        mask2 = num.ma.copy(data[portion]['x'].mask)
        
        data[portion]['OutlierMask']=mask2
        
        # creating the outlier + transit mask
        mask3 = num.ma.mask_or(data[portion]['TransitMask'],mask2)
        
        dout[portion] = {'kid':data[portion]['kid'],'x':data[portion]['x'],'y':data[portion]['y'],'yerr':data[portion]['yerr'],'TransitMask':data[portion]['TransitMask'],'UnMasked':data[portion]['UnMasked'],'OutlierMask':data[portion]['OutlierMask'],'OTMask':mask3}
        
    return dout

def ApplyMask(data,mask):
	""" This function applies a given mask """
	
        # loop through portions
	for portion in data.keys():
                # match data keys and apply mask

		for key in data[portion].keys():
			if key in 'xyerr':
                            if mask != 'UnMasked':
                                data[portion][key].mask = data[portion]['UnMasked']
                            data[portion][key].mask = data[portion][mask]
				
	
	return data