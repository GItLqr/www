#-*- coding: utf8 -*-
import sys
import web
import logging
import logging.config
import json
import time
from urllib2 import urlopen
from xml.etree import ElementTree as ET

# getLogger
logger = logging.getLogger()

weatherScPrefixStr = 'weather26DB5BBD-20AB-4d38-88AE-2D13110EABAE'
weatherScSubfixStr = '</Root>'
weatherStrDict = {}
weatherStrDict["暴雪"] = "baoxue"
weatherStrDict["暴雨"] = "baoyu"
weatherStrDict["大暴雨"] = "dabaoyu"
weatherStrDict["大雪"] = "daxue"
weatherStrDict["大雨"] = "dayu"
weatherStrDict["大雨"] = "dongyu"
weatherStrDict["多云"] = "duoyun"
weatherStrDict["浮尘"] = "fuchen"
weatherStrDict["雷阵雨"] = "leizhenyu"
weatherStrDict["雷阵雨伴有冰雹"] = "leizhenyubanyoubingbao"
weatherStrDict["强沙尘暴"] = "qiangshachenbao"
weatherStrDict["晴"] = "qing"
weatherStrDict["沙尘暴"] = "shachenbao"
weatherStrDict["特大暴雨"] = "tedabaoyu"
weatherStrDict["雾"] = "wu"
weatherStrDict["小雪"] = "xiaoxue"
weatherStrDict["小雨"] = "xiaoyu"
weatherStrDict["扬沙"] = "yangsha"
weatherStrDict["阴"] = "yin"
weatherStrDict["雨夹雪"] = "yujiaxue"
weatherStrDict["阵雪"] = "zhenxue"
weatherStrDict["阵雨"] = "zhenyu"
weatherStrDict["中雪"] = "zhongxue"
weatherStrDict["中雨"] = "zhongyu"
weatherStrDict["中到大雨"] = "dayu"
weatherStrDict["大到暴雨"] = "baoyu"
weatherStrDict["小到中雨"] = "zhongyu"
weatherStrDict["小到中雪"] = "zhongxue"
weatherStrDict["中到大雪"] = "daxue"
weatherStrDict["大到暴雪"] = "baoxue"
weatherStrDict["大到暴雪"] = "dabaoyu"
weatherStrDict["大暴到特大暴雨"] = "tedabaoyu"

weekTup = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

def calcIcon( weather, isBigIcon, isDay ):
    weather = weather.encode("utf8")
    weaStr = weatherStrDict[weather]
    if True == isBigIcon:
        res = "b"
    else:
        res = "s"
    if False == isDay and ( "qing" == weaStr or "duoyun" == weaStr ):
        res += "n_"
    else:
        res += "d_"
    res += weaStr
    return res

def getTodayForcast( forcastList ):
    data = {}
    data["id"] = ""
    curTimeTup = time.localtime(time.time())
    curHour = curTimeTup[3]
    if curHour >= 6 and curHour <= 18 :
        data["temperature"] = forcastList[0].find("temperature").text+"-"+forcastList[1].find("temperature").text
        data["dayIcon"] = calcIcon( forcastList[0].find("weather").text, True, True )
        data["nightIcon"] = data["dayIcon"]
        startIdx = 2
    else:
        data["temperature"] = forcastList[0].find("temperature").text
        data["nightIcon"] = calcIcon( forcastList[0].find("weather").text, True, False )
        data["dayIcon"] = data["nightIcon"]
        startIdx = 1
    data["week"] = ""
    data["weather"] = forcastList[0].find("weather").text+" "+forcastList[0].find("wind_direct").text+" "+forcastList[0].find("wind_power").text
    data["weather"] = data["weather"].encode("utf8")
    return data,startIdx
        
def getFutureForcast( forcastList, startIdx, dayCnt ):
    dataList = []
    for i in xrange(0, dayCnt):
        morningIdx = startIdx+i*2
        eveningIdx = startIdx+i*2+1
        datetime = forcastList[morningIdx].get("datetime")
        timeTup = time.strptime(datetime, "%Y-%m-%d %H:%M:%S")
        fWeek = timeTup[6]
        data = {}
        data["week"] = weekTup[int(fWeek)]
        data["week"] = data["week"].encode("utf8") if isinstance( data["week"], unicode) else  data["week"]
        data["id"] = ""
        data["temperature"] = forcastList[morningIdx].find("temperature").text+"-"+forcastList[eveningIdx].find("temperature").text
        data["dayIcon"] = calcIcon( forcastList[morningIdx].find("weather").text, False, True )
        data["nightIcon"] = calcIcon( forcastList[eveningIdx].find("weather").text, False, False )
        data["weather"] = forcastList[morningIdx].find("weather").text+" "+forcastList[morningIdx].find("wind_direct").text+" "+forcastList[morningIdx].find("wind_power").text
        data["weather"] = data["weather"].encode("utf8")
        dataList.append(data)
    return dataList

def getWeatherXmlStr( xmlStr ):
        weatherStrIndex = xmlStr.find( weatherScPrefixStr )
        if weatherStrIndex is -1:
            logger.error( "Weather service doesn't return weather, \n returned string [%s]" % xmlStr)
            return ""
        weaStartIndex = weatherStrIndex + len(weatherScPrefixStr)
        weaEndIndex = xmlStr.find( weatherScSubfixStr )
        if weaEndIndex is -1:
            logger.error( "Weather service returns invalid xml string, \n returned string [%s]" % xmlStr)
            return ""
        weaEndIndex += len(weatherScSubfixStr)
        weatherXmlStr = xmlStr[weaStartIndex:weaEndIndex]
        return weatherXmlStr
    
def getLocalWeather ( city ):
    try:
        apiUrl = "http://10.230.225.34:9080/?st=web&q=天气&loc=%s&vendor=100003" % city
        logger.debug( "opening weather sc %s" % apiUrl )
        xmlStr = urlopen(apiUrl, timeout=2.0).read()
        weaXmlStr = getWeatherXmlStr( xmlStr )
        if weaXmlStr is "":
            return [], 0, city
        weatherDataList = []
        root = ET.fromstring(weaXmlStr)
        cityNode = root.find("hits").find("hit").find("city");
        retCity = cityNode.get("name")
        forcastList = cityNode.findall("forcast")
        data, startIdx = getTodayForcast(forcastList)
        weatherDataList.append(data)
        dataList = getFutureForcast(forcastList, startIdx, 3)
        for i in xrange(0,len(dataList)):
            weatherDataList.append(dataList[i])
    except:
        logger.error( str(sys.exc_info()) )
        return [], 0, city
    return weatherDataList, int(time.mktime(time.strptime(forcastList[0].get("datetime"), "%Y-%m-%d %H:%M:%S"))), retCity

if __name__ == '__main__':
    dataList, unixTime, retCity = getLocalWeather('黑龙江省')
    print json.dumps(dataList, ensure_ascii=False)
    print unixTime
    print retCity
