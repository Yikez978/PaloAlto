from Rules import *
from Reports import *
import urllib
import httplib
from time import sleep
class PaAPI:
    '''
    Class for communicating with the PaloALto

        Authors:
            David Rice riceda@potsdam.edu
        Last Updated:
            01/29/2015 
    '''
    
    ##### Global Variables #####
    apiKey = ""
    baseURL = ""
    rules = []
    report = []
 
    ##### Public Methods #####
    '''
    Constructor: Will setup the connection to the PaloAlto 
    
        Constructor args:
            apiKeyFile => file name containing the PaloAlto API configs (string)
    '''
    def __init__(self, apiKeyFile):
        self.__importConfigFile(apiKeyFile)
        self.__loadFireWallRules()
        
    ### Methods for establishing a connection with the PaloAlto ###
    # This method will import the PaloAlto API key so the XMLAPI can be used
    def __importConfigFile (self, apiKeyFile):
        myFile = open(apiKeyFile, 'r')
        
        for line in myFile:
            if line.startswith("baseurl"):
                self.baseURL = line.split("=")[1].rstrip()
                if not self.baseURL.endswith("/"):
                    self.baseURL = self.baseURL + "/"
            elif line.startswith("apikey"):
                self.apiKey = line.split("=")[1].rstrip()# + "=="
    
    
    ### Methods for importing and instantiating pre-existing FireWall Rules from the PaloAlto as Rule objects ###
    # getFireWallRulesALL: will return a dictionary of all of the current PaloAlto firewall rules
    def __loadFireWallRules(self):
        root = self.__getFireWallRulesRoot()
        self.rules = []
        for child in root.iter('entry'):
            self.rules.append(
                    Rules(
                        self.__getRuleName(child), 
                        self.__getRuleFrom(child), 
                        self.__getRuleTo(child), 
                        self.__getRuleSource(child), 
                        self.__getRuleDestination(child), 
                        self.__getRuleService(child), 
                        self.__getRuleApplication(child),
                        self.__getRuleAction(child),
                        self.__getRuleSourceUser(child),
                        self.__getRuleDisableServerResponse(child),
                        self.__getRuleNegateSource(child),
                        self.__getRuleNegateDestination(child),
                        self.__getRuleDisabled(child), 
                        self.__getRuleGroup(child), 
                        self.__getRuleHipProfile(child), 
                        self.__getRuleLogStart(child), 
                        self.__getRuleLogEnd(child),
                        self.__getRuleDescription(child),
                        )
                    )

    
    '''
    getFireWallRules: will return a list of all of the Rule objects
    '''
    def getFireWallRules(self):
        return self.rules

        
    '''
    getFireWallRule: will return a Rule objects based on the rules name
    
        getFireWallRule args: 
            ruleName => name of the rule (string)
    '''
    def getFireWallRule(self, ruleName):
        for rule in self.rules:
            if rule.name == ruleName:
                return rule
        raise ValueError("Object does not exist")
    
    # This method will return the root of the PaloALto firewall rules for parsing the XML file provided by __getFireWallRulesXML
    def __getFireWallRulesRoot(self):
        paRules = self.__getFireWallRulesXML()
        import xml.etree.ElementTree as ET
        return ET.fromstring(paRules)
    
    # This method will return the PaloALto firewall rules in XML format
    def __getFireWallRulesXML (self):
        paRules = self.__readWebPage(self.baseURL + "api/?type=config&action=show&key=" + self.apiKey + "&xpath=/config/devices/entry/vsys/entry/rulebase/security/rules")
        return paRules



    '''
    createFireWallRule: will create and return a Rule object
    
        createFireWallRule args: 
            name => name of the rule (string)
            memFrom => from members of the rule (list of strings => zones)
            memTo => to members of the rule (list of strings => zones)
            src => sources of the rule (list of strings)
            dst => destination of the rule (list of strings)
            srv => services of the rule (list of strings)
            app => applications of the rule (list of strings)
            act => action of the rule (string => 'allow' or 'deny')
            srcUsr => source users of the rule (list of strings)
            disRsp => disable server response of the rule (string => 'yes' or 'no')
            negSrc => negate sources of the rule (string => 'yes' or 'no')
            negDst => negate destinations of the rule (string => 'yes' or 'no')
            disable => disable the rule (string => 'yes' or 'no')
            group => groups of the rule (list of strings)
            hipProf => hip-profiles of the rule (list of strings)
            logStart => start the log of the rule (string => 'yes' or 'no')
            logEnd => end the log of the rule (string => 'yes' or 'no')
            desc => description of the rule (string)
        '''
    def createFireWallRule(self, name, memFrom, memTo, src, dst, srv, app, act, srcUsr, disRsp, negSrc, negDst, disable, group, hipProf, logStart, logEnd, desc):
        newRule = Rules(name, memFrom, memTo, src, dst, srv, app, act, srcUsr, disRsp, negSrc, negDst, disable, group, hipProf, logStart, logEnd, desc)
        self.rules.append(newRule)
        return newRule
    
    
    ### Methods for Deleting FireWall Rules from the PaloAlto using Rule objects ###
    '''
    deleteFireWallRule: will create and submit the URL for deleting a PaloAlto FireWall Rule
    
        deleteFireWallRule args:
            rule => rule you want to delete (rule object)
    '''
    def deleteFireWallRule(self, rule):
        url = self.baseURL + "api/?type=config&action=delete&key=" + self.apiKey
        url = url + "&xpath=/config/devices/entry/vsys/entry/rulebase/security/rules/entry[@name='"+ rule.getRuleName() + "']"
        paResponse = self.__readWebPage(url)
        paRoot = self.__getWriteResponseRoot(paResponse)
        
        for subRoot in paRoot.iter('response'):
            for msg in subRoot:
                if msg.text == "command succeeded":
                    return msg.text
                else:
                    raise ValueError(msg.text)
        
        
    ### Methods for committing changes to the PaloAlto ###
    '''
    commitFireWallConfiguration: will create and submit the URL for committing changes to the PaloAlto
    '''
    def commitFireWallConfiguration(self):
        url = self.baseURL + "api/?type=commit&key=" + self.apiKey + "&cmd=<commit></commit>"
        paResponse = self.__readWebPage(url)
        paRoot = self.__getWriteResponseRoot(paResponse)
        
        # Parsing the XML Response to confirm whether the commit took place or not
        for msg in paRoot.iter('response'):
            if msg[0].text and msg[0].text == "There are no changes to commit.":
                return msg[0].text
            
            elif msg[0][0].text and "Another commit" in msg[0][0].text:
                print(".")
                sleep(5)
                self.commitFireWallConfiguration()
            elif msg[0][0][0].text and"Commit job" in msg[0][0][0].text:
                return msg[0][0][0].text
            
            else:
                raise ValueError(msg[0].text)
    
    ### Methods for writing a FireWall Rule to the PaloAlto ###
    '''
    writeFireWallRule: will create and submit the URL for writing a PaloAlto FireWall Rule
    
        writeFireWallRule args:
            rule => rule you want to write (rule object)
    '''
    def writeFireWallRule(self, rule):
        url = self.__buildFireWallRulesXML(rule)
        paResponse = self.__readWebPage(url)
        
        paRoot = self.__getWriteResponseRoot(paResponse)
        
        # Parsing the XML Response to confirm whether the commit took place or not
        for subRoot in paRoot.iter('response'):
            for msg in subRoot:
                if msg.text == "command succeeded":
                    return msg.text
                else:
                    raise ValueError(msg[0].text)
        
        return paRoot

    # This method will create XML to be used to generate a PaloALto firewall rule
    def __buildFireWallRulesXML (self, rule):
        url = self.baseURL + "api/?type=config&action=set&key=" + self.apiKey
        url = url + "&xpath=/config/devices/entry/vsys/entry/rulebase/security/rules/entry" + rule.genRuleNameXML()
        url = url + "&element="
        url = url + rule.genRuleFromMembersXML()
        url = url + rule.genRuleToMembersXML()
        url = url + rule.genRuleSourceXML()
        url = url + rule.genRuleDestinationXML()
        url = url + rule.genRuleServiceXML()
        url = url + rule.genRuleApplicationXML()
        url = url + rule.genRuleActionXML()
        url = url + rule.genRuleSourceUserXML()
        url = url + rule.genRuleDisableServerResponseXML()
        url = url + rule.genRuleNegateSourceXML()
        url = url + rule.genRuleNegateDestinationXML()
        url = url + rule.genRuleDisabledXML()
        url = url + rule.genRuleGroupsXML()
        url = url + rule.genRuleHipProfilesXML()
        url = url + rule.genRuleLogStartXML()
        url = url + rule.genRuleLogEndXML()
        url = url + rule.genRuleDescriptionXML()
        return url
    
    
    ### Methods for reading WebPages ###
    # This method will return the html of a provided url    
    def __readWebPage(self, queryPage):
        try:
            response = urllib.urlopen(queryPage)
            html = response.read()
            return html
        except httplib.BadStatusLine:
            pass
    
    def __getWriteResponseRoot (self, resp):
        import xml.etree.ElementTree as ET
        return ET.fromstring(resp)
    
    
    ### Parse XML Methods ###
    # Return the name of a Rule
    def __getRuleName(self, root):
        return root.get('name')
    
    # This method will return the 'from' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleFrom(self, root):
        retAttr = []
        for attrs in root.iter('from'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'to' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleTo(self, root):
        retAttr = []
        for attrs in root.iter('to'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'source' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleSource(self, root):
        retAttr = []
        for attrs in root.iter('source'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
        
    # This method will return the 'destination' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleDestination(self, root):
        retAttr = []
        for attrs in root.iter('destination'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'service' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleService(self, root):
        retAttr = []
        for attrs in root.iter('service'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'application' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleApplication(self, root):
        retAttr = []
        for attrs in root.iter('application'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'action' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleAction(self, root):
        retAttr = ""
        for attr in root.iter('action'):
                retAttr = attr.text
        return retAttr
        
    # This method will return the 'source-user' attribute from the PaloAlto API when provided correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleSourceUser(self, root):
        retAttr = []
        for attrs in root.iter('source-user'):
            for attr in attrs:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'disable-server-response-inspection' attribute from the PaloAlto when provided correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleDisableServerResponse(self, root):
        retAttr = ""
        for attr in root.iter('option'):
            retAttr = attr[0].text
        if retAttr:
            return retAttr
        else:  
            return "no"
    
    # This method will return the 'negate-source' attribute from the PaloAlto when provided correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleNegateSource(self, root):
        retAttr = ""
        for attr in root.iter('negate-source'):
            retAttr = attr.text
        if retAttr:
            return retAttr
        else:
            return "no"
    
    # This method will return the 'negate-destination' attribute from the PaloAlto when provided correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleNegateDestination(self, root):
        retAttr = ""
        for attr in root.iter('negate-destination'):
            retAttr = attr.text
        if retAttr:
            return retAttr
        else:
            return "no"
        
    # This method will return the 'disabled' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleDisabled(self, root):
        retAttr = ""
        for attr in root.iter('disabled'):
            retAttr = attr.text
        if retAttr:
            return retAttr
        else:
            return "no"
    
    # This method will return the 'group' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleGroup(self, root):
        retAttr = []
        for attrs in root.iter('profile-setting'):
            for attr in attrs[0]:
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'hip-profiles' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleHipProfile(self, root):
        retAttr = []
        for attrs in root.iter('hip-profiles'):
            for attr in attrs:    
                retAttr.append(attr.text)
        return retAttr
    
    # This method will return the 'log-start' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleLogStart(self, root):
        retAttr = ""
        for attr in root.iter('log-start'):
                retAttr = attr.text
        if retAttr:
            return retAttr
        else:
            return "no"
        
    # This method will return the 'log-end' attribute from the PaloAlto API when provided the correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleLogEnd(self, root):
        retAttr = ""
        for attr in root.iter('log-end'):
                retAttr = attr.text
        if retAttr:
            return retAttr
        else:
            return "no"   
    
    # This method will return the 'description' attribute from the PaloAlto when provided correct root (see getFireWallRule/getFireWallRulesALL as examples)
    def __getRuleDescription(self, root):
        retAttr = ""
        for attr in root.iter('description'):
            retAttr = attr.text
        if retAttr:
            return retAttr
        else:
            return ""
    
    
    
    
    
    
    
    ### Methods for getting reports from the PaloAlto ###
    def getReport(self, reportName):
        self.__loadReport(reportName)
        return self.report
    
    def __loadReport(self, reportName):
        root = self.__getReportRoot(reportName)
        self.report = []
        reportAttrs = []
        reportAttrFields = {}
        for child in root.iter('entry'):
            for subchild in child:
                reportAttrFields[subchild.tag] = subchild.text
            reportAttrs.append(reportAttrFields)
        Reports(
            reportName,
            reportAttrs
            )
    
    # This method will return the root of the PaloALto report for parsing the XML file provided by getReportXML
    def __getReportRoot(self, reportName):
        paReport = self.__getReportXML(reportName)
        import xml.etree.ElementTree as ET
        return ET.fromstring(paReport)
    
    def __getReportXML(self, reportName):
        reports = [
                   "bandwidth-trend", "botnet", "hruser-top-applications", "hruser-top-threats", "hruser-top-url-categories", 
                   "risk-trend", "risky-users", "spyware-infected-hosts", "threat-trend", "top-application-categories", 
                   "top-applications", "top-attackers", "top-attackers-by-countries", "top-attacks", "top-blocked-url-categories", 
                   "top-blocked-url-user-behavior", "top-blocked-url-users", "top-blocked-websites", "top-connections", 
                   "top-denied-applications", "top-denied-destinations", "top-denied-sources", "top-destination-countries", 
                   "top-destinations", "top-egress-interfaces", "top-egress-zones", "top-http-applications", "top-ingress-interfaces", 
                   "top-ingress-zones", "top-rules", "top-source-countries", "top-sources", "top-spyware-threats", 
                   "top-technology-categories", "top-url-categories", "top-url-user-behavior", "top-url-users", "top-users", 
                   "top-victims", "top-victims-by-countries", "top-viruses", "top-vulnerabilities", "top-websites", 
                   "unknown-tcp-connections", "unknown-udp-connections", "wildfire-file-digests"
                   ]
        
        if reportName in reports:
            url = self.baseURL + "api/?type=report&reporttype=predefined&reportname=" + reportName + "&key=" + self.apiKey
            paReport = self.__readWebPage(url)
            return paReport
        else:
            repList = ""
            for rep in reports:
                repList = repList + rep + "  "
            raise ValueError("Report name '" + reportName + "' does not exist.  You must use one of these reports:\n" + repList)
    
    
    
    
    def getDynamicReport(self, reportName, period, topN):
        self.__loadDynamicReport(reportName, period, topN)
        return self.report
    
    def __loadDynamicReport(self, reportName, period, topN):
        root = self.__getDynamicReportRoot(reportName, period, topN)
        self.report = []
        reportAttrs = []
        reportAttrFields = {}
        for child in root.iter('entry'):
            for subchild in child:
                reportAttrFields[subchild.tag] = subchild.text
            reportAttrs.append(reportAttrFields)
        Reports(
            reportName,
            reportAttrs
            )
    
    # This method will return the root of the PaloALto report for parsing the XML file provided by getReportXML
    def __getDynamicReportRoot(self, reportName, period, topN):
        paReport = self.__getDynamicReportXML(reportName, period, topN)
        import xml.etree.ElementTree as ET
        return ET.fromstring(paReport)    
    
    def __getDynamicReportXML(self, reportName, period, topN):
        reports = [
                   #"custom-dynamic-report",
                   "acc-summary", "top-app-summary", "top-application-categories-summary", "top-application-risk-summary", 
                   "top-application-subcategories-summary", "top-application-tech-summary", "top-applications-summary", "top-applications-trsum", 
                   "top-attacker-countries-summary", "top-attackers-summary", "top-attacks-acc", "top-blocked-url-categories-summary", "top-blocked-url-summary", 
                   "top-blocked-url-user-behavior-summary", "top-data-dst-countries-summary", "top-data-dst-summary", "top-data-egress-zones-summary", 
                   "top-data-filename-summary", "top-data-filetype-summary", "top-data-ingress-zones-summary", "top-data-src-countries-summary", 
                   "top-data-src-summary", "top-data-type-summary", "top-dst-countries-summary", "top-dst-summary", "top-egress-zones-summary", 
                   "top-hip-objects-details", "top-hip-objects-summary", "top-hip-profiles-details", "top-hip-profiles-summary", "top-hip-report-links", 
                   "top-hr-applications-summary", "top-ingress-zones-summary", "top-rule-summary", "top-spyware-download-summary", "top-spyware-phonehome-summary", 
                   "top-spyware-threats-summary", "top-src-countries-summary", "top-src-summary", "top-threat-egress-zones-summary", "top-threat-ingress-zones-summary", 
                   "top-threats-type-summary", "top-url-categories-summary", "top-url-summary", "top-url-user-behavior-summary", "top-victim-countries-summary", 
                   "top-victims-summary", "top-viruses-summary", "top-vulnerabilities-summary"
                   ]
        
        periods = [
                   "last-60-seconds", "last-15-minutes", "last-hour", "last-12-hrs", "last-24-hrs", "last-calendar-day", "last-7-days", "last-7-calendar-days",
                   "last-calendar-week", "last-30-days"
                   ] 
        
        if reportName in reports:
            url = self.baseURL + "api/?type=report&reporttype=dynamic&reportname=" + reportName
            
            if period in periods:
                url = url + "&period=" + period
            else:
                if period:
                    perList = ""
                    for per in periods:
                        perList = perList + per + " "
                    raise ValueError("The period value '" + period + "' does not exist, use one of the following:\n" + perList)
            if topN and topN.isdigit():
                url = url + "&topn=" + topN
            elif topN and not topN.isdigit():
                raise ValueError("The topN value must be an integer")
                                
            url = url + "&key=" + self.apiKey
            paReport = self.__readWebPage(url)
            return paReport
        else:
            repList = ""
            for rep in reports:
                repList = repList + rep + "  "
            raise ValueError("Report name '" + reportName + "' does not exist.  You must use one of these reports:\n" + repList)
