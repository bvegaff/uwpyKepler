#!/astro/apps/pkg/python64/bin//python

import uwpyKepler as kep
import sys
import numpy as num
import pylab
import optparse
import os

def sharexPlot(lc):
    lcData = lc.lcFinal
    idx = num.where(lcData['eMask'] == 1)[0]
    tx = lcData['x'][idx]
    ty = lcData['y'][idx]
    tydt = lcData['ydt'][idx]
    ax1 = pylab.subplot(211)
    pylab.title('KID: %s' % kid)
    pylab.ylabel('Flux')
    pylab.plot(lcData['x'], lcData['y'], 'b.')
    pylab.plot(lcData['x'], lcData['correction'], 'k.')
    pylab.plot(tx, ty, 'ro')
    ax2 = pylab.subplot(212, sharex=ax1)
    pylab.xlabel('BJD')
    pylab.ylabel('CorrFlux')
    pylab.plot(lcData['x'], lcData['ydt'], 'b.')
    pylab.plot(tx, tydt, 'ro')
    
def foldPlot(lc):
    period = lc.eData['KOI']['fake']['Period']
    t0 = lc.eData['KOI']['fake']['T0']
    lcData = lc.lcFinal
    phase = kep.func.foldPhase(\
        lcData['x'], t0 + 0.5 * period, period)
    pylab.title('KID: %s' % kid)
    pylab.ylabel('CorrFlux')
    pylab.xlabel('Phase')
    idx = num.where(lcData['eMask'] == 1)[0]
    tphase = phase[idx]
    ty = lcData['ydt'][idx]
    pylab.plot(phase, lcData['ydt'], 'b.')
    pylab.plot(tphase, ty, 'ro')


kid = sys.argv[1]
if __name__ == '__main__':
    parser = optparse.OptionParser(usage=\
    "%prog\nUse this script to make various lightcurve plots,\nmasking transits using eclipse data from file:\n\t/astro/store/student-scratch1/johnm26/dFiles/eDataDiscoveries.txt\nScript requires a Kepler ID as a system argument.")
    parser.add_option('-f','--fold',\
                        action='store_true',\
                        dest='fold',\
                        default=False,\
                        help='fold the lightcurve')
    parser.add_option('-t','--findT0',\
                        action='store_true',\
                        dest='findT0',\
                        default=False,\
                        help='enter interactive t0 resetter')
    parser.add_option('-b','--binary',\
                        action='store_true',\
                        dest='binary',\
                        default=False,\
                        help='tells script to read from or' \
                        'write to binary eData file')
    parser.add_option('-a','--append',\
                        action='store_true',\
                        dest='append',\
                        default=False,\
                        help='when -t selected, tells script' \
                        'to append to eData file')
    cChoice = ('LC','SC','')
    parser.add_option('-c','--ctype',\
                        choices=cChoice,\
                        type='choice',\
                        dest='ctype',\
                        default='LC',\
                        help='The expected cadence type('\
                        +', '.join(cChoice)\
                        +') [default: %default]')

    opts, args = parser.parse_args()
    period, t0, q = kep.analysis.geteDataFromFile(kid, binary=opts.binary)
    lc = kep.keplc.keplc(kid)
    lc.eData['eDataExists'] = True
    lc.eData['KOI'] = {'fake':\
                      {'Period':period, 'T0':t0, 'Duration':q}}
    kw = kep.quicklc.quickKW(ctype=opts.ctype)
    lc.runPipeline(kw)
    lc.lcFinal['x'] = lc.lcFinal['x'] + lc.BJDREFI

    if opts.fold:
        foldPlot(lc)
        pylab.show()
    elif opts.findT0:
        foldPlot(lc)
        newt0 = kep.analysis.resetT0(t0, period)
        kep.analysis.writeEDataToFile(kid, period, newt0, q, \
            binary=opts.binary, append=opts.append)
        print 't0 reset to:', newt0
    else:
        sharexPlot(lc)
        pylab.show()
