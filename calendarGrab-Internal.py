# Needs Python3 - python3 calendarGrab.py
# pip3 install python-dateutil
# sudo python -m ensurepip --upgrade
# sudo pip install --upgrade pip  
# sudo pip3 install –upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# sudo pip3 install --upgrade --ignore-installed  google-api-python-client google-auth-httplib2 google-auth-oauthlib

# REFERENCE - 
# FOLLOW THIS! >>> : https://www.youtube.com/watch?v=1JkKtGFnua8 <<<
# Google from: https://learndataanalysis.org/google-py-file-source-code/
# Auth reference from: https://developers.google.com/calendar/api/guides/auth
# Event List: https://developers.google.com/calendar/api/v3/reference/events/list#python
# https://console.cloud.google.com/  /   https://console.cloud.google.com/apis/credentials?project=emea-sc-calendar-scrape

import datetime
from Google import Create_Service
import calendarGrabUtils

# tchinchen mlivermore gmoodley cfischer gsingh1

########################################
SCName = 'tchinchen'  # EDIT THIS WITH THE PAGERDUTY USER /EMAIL NAME
########################################


class ActivityRecord:
    def __init__(self, start, summary, meetingType, duration):
        self.start = start
        self.summary = summary
        self.meetingType = meetingType
        self.duration = duration


ActivityRecords = []


CLIENT_SECRET_FILE = 'token.json'
API_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME,API_VERSION, SCOPES)

#Opens 2 files - one for Debug and Noise - One for the actual output:
fDebug = open("CalendarCaptureInternalDEBUG.txt", "w")
fResults = open("~CalendarCaptureInternal-" + SCName + ".txt", "w")

#print(dir(service)) # Just checks all is running!

#Set up Event count
eventCount = 0

#========================================================================
#Define Start and End of Quarter: -
d = datetime.datetime(2021, 8, 1)
StartofQuarter = d.isoformat('T') + "Z"
d = datetime.datetime(2021, 10, 31)
EndofQuarter = d.isoformat('T') + "Z"
#========================================================================




#Call Google API
page_token = None
while True:

  events = service.events().list(calendarId=SCName+'@pagerduty.com', pageToken=page_token, timeMin=StartofQuarter, timeMax=EndofQuarter).execute()
  
  #For all returned Events
  for event in events['items']:
    meetingType = ''
    eventCount = eventCount + 1
    isIgnore = False
    isIgnoreReason = ""
    isRecruitment = False
    SCresponseStatus = ''

    try:
        
        fDebug.write('=========================================================================================\n\n')
        
        dutoniumCount = 0

        #==================================================
        # Get info about Attendees
        #==================================================        

        for attendee in event['attendees']:
            if "@pagerduty" not in attendee['email']:
                if not calendarGrabUtils.IsNonCustomerAccount(attendee['email']):
                    isIgnore = True # Is a Customer Meeting
                    isIgnoreReason = "CUSTOMER MEETING"
            else:
                dutoniumCount = dutoniumCount + 1

        for attendee in event['attendees']:
            #Recruiting meeting!
            if "lily.greenhouse.io" in attendee['email']:  
                isRecruitment = True
                meetingType = 'RECRUITMENT'
                isIgnore = False
                isIgnoreReason = ""
                isPersonal = False
                                 
        for attendee in event['attendees']:
            if SCName in attendee['email']:
                SCresponseStatus = attendee['responseStatus']

        #==================================================
        #Errors normally occur if the event is == 'status': 'cancelled'    
        try:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            startTime = start.split("T")[1][0:8]
        except KeyError as err:
            start = 'unknown'
        except IndexError as err:
            start = 'unknown'

        meetingLength = calendarGrabUtils.getMeetingLength(start,end)

        if not isRecruitment:
            eventSummary = event['summary'].lower().replace(',',' ')
            meetingType = calendarGrabUtils.GetInternalActivityType(eventSummary)

        if dutoniumCount == 2:
            meetingType = 'ONE TO ONE'
        if dutoniumCount > 2 and meetingType =='ONE TO ONE':
            meetingType = 'INTERNAL MEETING'
        if dutoniumCount > 20: #If a large Dutonium meeting assume there could be external emails on it! (We'll ignore if SC rejects!)
            isIgnore = False

        if isRecruitment:
            meetingType = "RECRUITMENT"

        eventOrganizer = event['organizer']['email']
        if eventOrganizer == SCName + 'pagerduty.com':
            isIgnore = False

        if calendarGrabUtils.ignoreActivity(eventSummary):
            isIgnore = True
            isIgnoreReason = "ON IGNORE LIST"

        if start == 'unknown':
            isIgnore = True
            isIgnoreReason = "INVALID START TIME"

        if (SCresponseStatus == 'declined'):
            isIgnore = True
            isIgnoreReason = "SC DECLINED"

        if (SCresponseStatus == 'needsAction'):
            isIgnore = True
            isIgnoreReason = "SC NO RESPONSE"

        if isIgnore:
            print(startTime + ',' + meetingType + ' RECORD ' + str(isIgnore) + ' - ' + eventSummary + ' --- (' + isIgnoreReason + ') #' + str(dutoniumCount))

        if not isIgnore:
            fResults.write(start[0:10] + ',' + eventSummary + ',' + meetingType + ',' + str(meetingLength) + '\n' )
            ActivityRecords.append(ActivityRecord(start[0:10],eventSummary,meetingType,meetingLength))

    except KeyError as err:
        errCount = 0
        #print ('Cannot Get Event' + str(err))

  page_token = events.get('nextPageToken')
  if not page_token:
    break

print(str(len(ActivityRecords)) + ' activity records found')

recruitmentTime = 0
enablementTime = 0
prepTime = 0
internalMeetingsTime = 0
marketingTime = 0
volTime = 0
oneToOne = 0 


for activity in ActivityRecords:
    if activity.meetingType == "ENABLEMENT":
        enablementTime = enablementTime + activity.duration
    if activity.meetingType == "RECRUITMENT":
        recruitmentTime = recruitmentTime + activity.duration
    if activity.meetingType == "WEBINAR":
        marketingTime = marketingTime + activity.duration
    if activity.meetingType == "VOLUNTEERING":
        volTime = volTime + activity.duration
    if activity.meetingType == "ONE TO ONE":
        oneToOne = oneToOne + activity.duration
    if activity.meetingType == "PREP":
        prepTime = prepTime + activity.duration
    if activity.meetingType == "INTERNAL MEETING":
        internalMeetingsTime = internalMeetingsTime + activity.duration


fResults.write('===================================================='+ '\n\n\n')
fResults.write('Recruiting,' + str(round(recruitmentTime/60))+ '\n')
fResults.write('Enablement,' + str(round(enablementTime/60))+ '\n')
fResults.write('Prep,' + str(round(prepTime/60))+ '\n')
fResults.write('Internal,' + str(round(internalMeetingsTime/60))+ '\n')
fResults.write('Marketing,' + str(round(marketingTime/60))+ '\n')
fResults.write('Volunteer,' + str(round(volTime/60))+ '\n')
fResults.write('One2One,' + str(round(oneToOne/60))+ '\n')



fDebug.close()
fResults.close()
print(str(eventCount) + ' events processed!')