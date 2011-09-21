#import difflib
import sys, os

def getUniqueTraceback(logFile):
    """
    sorts though exception log files and
    prints unique exceptions to separate files
    with a list of KIDs and input parameters.
    """
    
    file = open(logFile,'r')
    fileLines = file.readlines()
    
    erri = 0
    StartStack = False
    errDict = {}
    objDict = {}
    stkDict = {}
    Stack = ''
    StackList = []
    #Read through each line in the log
    for i in range(len(fileLines)):
        #Look for the start of a new error message
        #and start writing the lines of this message
        if fileLines[i].startswith('Traceback'):
            errDict[erri] = Stack
            stkDict[erri] = Stack
            StackList.append(Stack)
            erri += 1
            StartStack = True
            Stack = ''
        #Look for the start of the KID and 
        #input parameter notes and write these lines
        if fileLines[i].startswith('#'):
            objDict[erri] = fileLines[i]
            StartStack = False
        #Stack error lines
        if StartStack:
            Stack += fileLines[i]

    #print len(set(StackList[1:])), len(StackList[1:])
    #Get the set of unique bugs and write to file
    UniqueBugs = list(set(StackList[1:]))
    UBugFile = open('UniqueBug.log','w')
    FOList = []
    for i in range(len(UniqueBugs)):
        print >> UBugFile, '# '+str(i+1)
        print >> UBugFile, UniqueBugs[i]
        # Failed object (KID) list file
        bFileName = 'OBJ_BUG.'+str(i+1)+'.log'
        os.system('rm -v %s' % bFileName)
        FOList.append(open(bFileName,'a'))
        
    UBugFile.close()
    del errDict[0]
    
    for i in errDict.keys():
        for j in range(len(UniqueBugs)):
            if errDict[i] == UniqueBugs[j]:
                print >> FOList[j], objDict[i].strip('\n')
