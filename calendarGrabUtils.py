import datetime
import validators


#================================================================================================
def IsPersonalAccount(emailAddress):
    personalEmails = ["gmail","aol","hotmail","btinternet","icloud","outlook", "resource.calendar.google.com", "live.co.uk","insightsquared.com","yahoo.fr"]
    personalAccount = False

    for domain in personalEmails:
        if domain.lower() in emailAddress.lower():
            personalAccount = True

    return personalAccount




#================================================================================================
def IsNonCustomerAccount(emailAddress):
    personalEmails = ["argushd", "ecosystems", "argushd" , "weshape","goconsensus", "techshecan.org" , "chiefnation","sjpp", "hireheroesusa.org", "chezie.co", "operationgratitude", "gong.io", "outsourcedevents", "productgrowthleaders", "atelierkultur","2winglobal", "productgrowthleaders", "streamlinevents", "archetype.co", "youthalive.org", "caremessage.org", "trekmedics.org", "sirum.org", "nexleaf.org", "turn.io", "variacode", "jeli", "uptimelabs.io", "bcg.com","ktsl","hummingbirdrcc","catalystonline", "thevirtualcro", "techsalesadvisors","tommccarthy", "alvinisd.net", "themindgym", "wilsondow", "toasttab", "live.pt", "civir.es" ,"amazon", "cdsr.com", "cditrec.com","chime.aws","gremlin.com", "justinmrobbins.com","msn.com", "catalytic.com","group.calendar.google","forcemanagement.com"]
    NonCustomer = False


    for domain in personalEmails:
        if domain.lower() in emailAddress.lower():
            NonCustomer = True

    return NonCustomer



#================================================================================================
def GetCustomerActivityType(Summary):
    
    returnAtivity = "other"

    activities = {
            "monthly": "catch-up",
            "weekly": "catch-up",
            "session": "tech sync",
            "integration": "tech sync",
            "technical": "tech sync",
            "sync": "tech sync",
            "trial follow up": "tech sync",
            "working session": "tech sync",
            "overview": "demo",
            "set up": "tech sync",
            "review": "tech sync",
            "workshop": "workshop",
            "sync": "tech sync",
            "check-in": "tech sync",
            "pov": "pov",
            "poc": "pov",
            "current state": "workshop",
            "discovery": "discovery",
            "current state" : "workshop",
            "trial config": "pov",
            "scoping": "pov kick-off",
            "requirements": "pov kick-off",
            "kick": "pov kick-off",
            "intro": "demo",
            "introduction": "demo",
            "demo": "demo",
            "rfp": "rfp",
            "qbr": "qbr",
            "training": "training"
        }

    for activityKeyword,activityType in activities.items():
        #print('Is activity ' + activityKeyword + '?')
        if activityKeyword in Summary.lower():
            returnAtivity = activityType

    return returnAtivity

#================================================================================================
def GetInternalActivityType(Summary):
    
    returnAtivity = "INTERNAL MEETING"

    activities = {
            "monthly": "INTERNAL MEETING",
            "weekly": "INTERNAL MEETING",
            "task": "PREP",
            "/": "ONE TO ONE",
            ":": "ONE TO ONE",
            "connect": "ONE TO ONE",
            "qbr": "INTERNAL MEETING",
            "sc team meeting": "INTERNAL MEETING",
            "prep": "PREP",
            "volunteering": "VOLUNTEERING",
            "task": "PREP",
            "follow": "PREP",
            "demo": "WEBINAR",
            "lunch & learn": "WEBINAR",
            "webinar": "WEBINAR",
            "coffee club": "INTERNAL MEETING",
            "the moorgate bugle": "INTERNAL MEETING",
            "interview": "RECRUITMENT",
            ": 30 Minute Meeting": "RECRUITMENT",
            "enablement": "ENABLEMENT",
            "launch": "ENABLEMENT",
            "need to know": "ENABLEMENT",
            "101": "ENABLEMENT",            
            "training": "ENABLEMENT",
            "emea leadership summit": "ENABLEMENT",
            "1:1": "ONE TO ONE",
            "1 to": "'ONE TO ONE",            
            "one to": "ONE TO ONE"
        }

    for activityKeyword,activityType in activities.items():
        #print('Is activity ' + activityKeyword + '?')
        if activityKeyword.lower() in Summary.lower():
            returnAtivity = activityType

    return returnAtivity




#================================================================================================
def ignoreActivity(Summary):
    ignore = False
    activitiesToIgnore = ["pto","annual leave","day off","reminder","out of office",
        "wellness","yoga","holiday","leaving drinks","mental heath week", "room booking", "reserved"
    ]        

    for activiy in activitiesToIgnore:
        if activiy in Summary.lower():
            ignore = True

    return ignore
#================================================================================================




#================================================================================================
def getMeetingLength(start,end):

    meetingLength = 0
    try:
        endTime = end.split("T")[1][0:8]
        startTime = start.split("T")[1][0:8]
        FMT = '%H:%M:%S'
        meetingLength = (datetime.datetime.strptime(endTime, FMT) - datetime.datetime.strptime(startTime, FMT)).total_seconds() / 60.0
        #print(str(meetingLength))
    except KeyError as err:
        meetingLength = 0
    except IndexError as err:
        meetingLength = 0

    #To deal with an meetings that cross a day (APAC timed SC meetings!)
    if meetingLength < 0:
        meetingLength = 0

    return meetingLength



#================================================================================================
def getMeetingLocationType(loc):

    #print("Location IN " + loc)

    remoteLocations = ["Reunión de Microsoft Teams",
                "Teams Meeting",
                "Microsoft Teams Meeting",
                "webex",
                "London-3-Bank (2) [Zoom]",
                "Microsoft Teams-Besprechung",
                "London-3-Cockfosters (2) [Zoom]",
                "London-3-King's Cross (2) [Zoom]",
                "London-3-Kings Cross (2) [Zoom]", 
                "Microsoft Teams Meeting", 
                "London-3-Cockfosters (2)", 
                "Google Meet", 
                "CHIME", "Webex",
                "877-777-8895 pc:7343538",
                "TBD" ,
                "Virtual only", "Réunion Microsoft Teams",
                "Microsoft Teams", "Skype Meeting"
                "Webex", "Join Zoom Meeting",
                "Toronto-6-Liberty Village (2) [Zoom]",
                "SF-2-Pink Triangle (4) [Zoom]", "Zoom link embedded in the invite",
                "6th Floor (Yonge & Eglinton)", "Google Meet - meet.google.com/ood-wtgu-khq",
                "Lodz-4-Phonebooth (1)","Réunion par Teams","Microsoft Teams-Besprechung", "Reunión de Microsoft Teams","Webex call",
                "Reunión de Microsoft Teams", "WebEx", "Web Ex", "Webex, US-MHQ-4NW07-Vanilla Cone (7), US-MHQ-4SE01-McFlurry (6)",
                "OAK-16-Clue (Screen, Google Meet) (4)", "Réunion Microsoft Teams",
                "My Zoom","ZOOM ONLY  https://morganstanley.zoom.us/j/5673982238"]

    for locItem in remoteLocations:
        if locItem.lower() in loc.lower():
            #print("replacing " + locItem + " in " + loc)
            loc = loc.replace(locItem,'')


    loc = loc.replace(',','').replace('[','').replace(']','').replace("'","").replace('  ','').replace(' ','')

    valid = validators.url(loc)

    if valid==True:
        loc = "Remote"

    if loc.replace(" ", "") == "":
        outLocation = "Remote"
    else:
        outLocation = loc

    #print("Location:" + outLocation)

    return outLocation

