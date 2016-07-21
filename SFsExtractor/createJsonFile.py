#!/usr/bin/env python
import sys
import os
import re
from ROOT import TFile, TIter, TKey, TH2F, TH1F, TGraphAsymmErrors
import json
import pickle

args = sys.argv[1:]
if len(args) > 0: inputTree = args[0]
print "input tree=", inputTree

if len(args) > 1: outputJson = args[1]
print "output json=", outputJson

#from array import *
#import math
#import pickle


def getValueError(value, error, nameVar, meanVar):
    binEntry={}
    binEntry["value"]=value
    binEntry["error"]=error
    binEntry[nameVar]=meanVar
    return binEntry

def getHistoContentInJson(histo, theTGraphList):
    xBins={}
    histoName=histo.GetName()
    xaxisName = re.split("_",histoName)[0]
    yaxisName = re.split("_",histoName)[1]
    if (histo.GetYaxis().GetNbins()==1):
        print "this is a 1D histo",xaxisName
        for i in range(1,histo.GetXaxis().GetNbins()+1):
            #print "centerBinValue",theTGraphList[0].GetX()[i-1]
            #print "low Error =", theTGraphList[0].GetErrorXlow(i-1);
            #print "high Error =", theTGraphList[0].GetErrorXhigh(i-1);
            xBinValue=xaxisName+":["+str(histo.GetXaxis().GetBinLowEdge(i))+","+str(histo.GetXaxis().GetBinUpEdge(i))+"]"
            xBins[xBinValue]=getValueError(histo.GetBinContent(i), histo.GetBinError(i), xaxisName+"_mean",theTGraphList[0].GetX()[i-1])
    else :
        for i in range(1,histo.GetXaxis().GetNbins()+1):
            yBins={}
            xBinValue=xaxisName+":["+str(histo.GetXaxis().GetBinLowEdge(i))+","+str(histo.GetXaxis().GetBinUpEdge(i))+"]"
            for j in range(1,histo.GetYaxis().GetNbins()+1):
                yBinValue=yaxisName+":["+str(histo.GetYaxis().GetBinLowEdge(j))+","+str(histo.GetYaxis().GetBinUpEdge(j))+"]"
                yBins[yBinValue]=getValueError(histo.GetBinContent(i,j), histo.GetBinError(i,j),xaxisName+"_mean",theTGraphList[j-1].GetX()[i-1])
            xBins[xBinValue]=yBins
    return xBins

def appendTheTGraph(nameOfTH2F, nameOfDirectory):
    listOfTGraphs=[]
    directory = rootoutput.GetDirectory(nameOfDirectory)
    keyInDir = TIter(directory.GetListOfKeys())
    theKey = keyInDir.Next()
    while(theKey):
        if ((re.split("_",nameOfTH2F)[0]==re.split("_",theKey.GetName())[0]) and (theKey.GetClassName()=="TGraphAsymmErrors")):
            print "in appendTheTGraph: name="+theKey.GetName()+ " type="+theKey.GetClassName()+" beg="+ re.split("_",theKey.GetName())[0]
            theTGraph = rootoutput.Get(nameOfDirectory+"/"+theKey.GetName())
            listOfTGraphs.append(theTGraph)
        theKey = keyInDir.Next()
    return listOfTGraphs
data={}

rootoutput = TFile.Open(inputTree)
rootoutputTest = TFile.Open(inputTree)

nextkey = TIter(rootoutput.GetListOfKeys())
key = nextkey.Next()
while (key): #loop
    if key.IsFolder() != 1:
        continue
    print "will get the SF in the for ID/bis ", key.GetTitle()
    directory = rootoutput.GetDirectory(key.GetTitle())
    keyInDir = TIter(directory.GetListOfKeys())
    subkey = keyInDir.Next()
    efficienciesForThisID = {}
    while (subkey):
#        if "ratio" in subkey.GetName():
        subDirectory = rootoutput.GetDirectory(key.GetTitle()+"/"+subkey.GetName())
        keyInEffDir = TIter(subDirectory.GetListOfKeys())
        effkey = keyInEffDir.Next()
        while(effkey):
            print "name=",effkey.GetName()," type=",effkey.GetClassName()
            if (effkey.GetClassName()=="TH1F" or effkey.GetClassName()=="TH2F"):
                print "name=",effkey.GetName()," type=",effkey.GetClassName()
                theHistoPlot = rootoutput.Get(key.GetTitle()+"/"+subkey.GetName()+"/"+effkey.GetName())
                listTGraphs = []
                if (effkey.GetClassName()=="TH1F"):
                    nameTGraph= re.split("histo_",effkey.GetName())[1]
                    theTGraph = rootoutputTest.Get(key.GetTitle()+"/"+subkey.GetName()+"/"+nameTGraph)
                    listTGraphs.append(theTGraph)
                elif (effkey.GetClassName()=="TH2F"):
                    listTGraphs = appendTheTGraph(effkey.GetName(), key.GetTitle()+"/"+subkey.GetName())
                print "name of the graph will be:", effkey.GetName()
                efficienciesForThisID[effkey.GetName()] = getHistoContentInJson(theHistoPlot,listTGraphs)
            effkey = keyInEffDir.Next()
        subkey = keyInDir.Next()
    data[key.GetTitle()]=efficienciesForThisID
    key = nextkey.Next()


with open(outputJson,"w") as f:
    json.dump(data, f, sort_keys = False, indent = 4)

outputPickle = outputJson.replace('json', 'pkl')

with open(outputPickle,"w") as f:
    pickle.dump(data, f)
