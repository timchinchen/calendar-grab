# BIG TIP IF YOU GET 
# ('invalid_grant: Token has been expired or revoked.', {'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})
# Just delete the "token files" folder and it will force regeneration from:
# timchinchen@timchinchen-C02F9164ML85 calendar % python3 WhohaveIMet.py
# Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=152032588744-ecvrv7ovg5mi4a9vsgkfjma1nno32sb9.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&state=03p9H0MohhXidp42oIuBoeoXJZA3ru&access_type=offline
# calendar v3 service created successfully



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
import calendarGrabUtils

from Google import Create_Service





####################################################
#ALL SCs
SCs = ["tchinchen", "another01", "another02", "another03"]


# "jshie", "evelasco", "gfelipe",  


outputFile = "~CalendarCapture-GlobalSCs-FY24.csv"


AMER = ["another01", "another02"]
EMEA = ["tchinchen"]
APAC = ["another03"]




CLIENT_SECRET_FILE = 'token.json'
API_NAME = 'calendar'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/calendar']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME,API_VERSION, SCOPES)

#Opens 2 files - one for Debug and Noise - One for the actual output:
fDebug = open("CalendarCaptureDEBUG.txt", "w")
fResults = open(outputFile, "w")

fResults.write('SC Name, Team ,Date,Time,Account,Event Type,Duration,PD Accepted,Customer Attended,IsRecurring,Remote,Address,PD Count,PD Attendees\n')


cantReadSC = ""

overallEventCount = 0

for SC in SCs:

    ########################################
    SCName = SC  # EDIT THIS WITH THE PAGERDUTY USER /EMAIL NAME
    ########################################

    #print(dir(service)) # Just checks all is running!

     #Define Start and End of Quarter: -
    Sd = datetime.datetime(2025, 1, 1)
    StartofQuarter = Sd.isoformat('T') + "Z"
    Ed = datetime.datetime(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day)
    EndofQuarter = Ed.isoformat('T') + "Z"

    #Set up Event count
    eventCount = 0
    SCeventCount = 0
    errCount = 0

    #Call Google API
    page_token = None
    while True:

        #Ensure you use "singleEvents=True" to catch repeating events.  /   orderBy='updated' , singleEvents=False    
        events = service.events().list(calendarId=SCName+'@pagerduty.com', orderBy='updated' , singleEvents=False, pageToken=page_token, timeMin=StartofQuarter, timeMax=EndofQuarter, maxResults=99999).execute()

        TeamName = ""
        if SCName in AMER:
            TeamName = "AMER"
        if SCName in EMEA:
            TeamName = "EMEA"      
        if SCName in LEAD:
            TeamName = "LEAD"
        if SCName in APAC:
            TeamName = "APAC"
        if SCName in Specialist:
            TeamName = "Specialist"        


        time_date_event_list = []

        #For all returned Events
        for event in events['items']:

            eventCount = eventCount + 1
            PDCount = 0
            PDAttendees = ""

            try:
                fDebug.write('=========================================================================================\n\n')

                #print('\n' + str(event) + '\n')
                #fDebug.write(str(event) +'\n')

                #Errors normally occur if the event is == 'status': 'cancelled'    
                try:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    startTime = start.split("T")[1][0:8]
                    meetingLength = calendarGrabUtils.getMeetingLength(start,end)
                except KeyError as err:
                    start = 'unknown'
                except IndexError as err:
                    start = 'unknown'


                eventSummary = event['summary'].lower()
                eventOrganizer = event['organizer']['email'].lower()

                try: 
                    recurrence = str(event['recurrence']).lower()
                    recurrence = 'TRUE'
                except KeyError as err:
                    recurrence = 'FALSE'

                
                company = []
                SCAttended = True
                PDresponseStatus = ''
                CustomerAttended = 'Customer Not Confirmed'
                CustomerresponseStatus = ''

                for attendee in event['attendees']:

                    if SCName in attendee['email']:
                        #Check the SC didn't decline:
                        PDresponseStatus = attendee['responseStatus']
                        #print(SCName + ' ' + PDresponseStatus)
                        if PDresponseStatus == 'declined':
                            SCAttended = False
                        #if PDresponseStatus == '': # Edge case - The Calendar invite is created by the SC but they remove themselves!
                        #    SCAttended = False

                    #Recruitment:
                    if "lily.greenhouse.io" in attendee['email']:                        
                        SCAttended = False

                    #Remove any trash emails!!!
                    if "pagerduty" not in attendee['email']:
                        if "rundeck" not in attendee['email']:

                            if not calendarGrabUtils.IsPersonalAccount(attendee['email']):
                                if not calendarGrabUtils.IsNonCustomerAccount(attendee['email']):

                                    attendeeCompany = attendee['email'].split("@",1)[1]

                                    if (attendeeCompany not in company):
                                        
                                        CustomerresponseStatus = attendee['responseStatus']     
                                        if CustomerresponseStatus == 'accepted':
                                            CustomerAttended = 'Customer Confirmed'                                                  
                                        company.append(attendeeCompany) 
                    if "pagerduty" in attendee['email']:
                        PDCount = PDCount + 1
                        PDAttendees = PDAttendees + '|' +  attendee['email'].replace("@pagerduty.com","")

                #Assumption - if sent from a Customer they will have confirmed
                if "pagerduty" not in eventOrganizer:
                    CustomerAttended = 'Customer Confirmed' 


                if len(company) > 0:

                    eventType = calendarGrabUtils.GetCustomerActivityType(eventSummary)

                    if SCAttended:
                        opp = str(company)
                        opp = opp.replace(',',' ').replace('[','').replace(']','').replace("'","").replace('  ',' ')
                        opp = opp.replace('.com','').replace('.co.uk','').replace('.fr','').replace('.au','').replace('.co.jp','').replace('.de','').replace('.gov','')
                        eventSummary = eventSummary.replace(',',' ').replace('[','').replace(']','').replace("'","").replace('  ',' ')


                        try:
                            if start.endswith('Z'):
                                strStart = start.replace("T", " ").replace("Z", "")
                            elif "+" in start:
                                size = len(start)
                                dashLocation = size - start.rfind('+')
                                strStart = start.replace("T", " ")[:size - dashLocation]
                            else:
                                size = len(start)
                                dashLocation = size - start.rfind('-')
                                strStart = start.replace("T", " ")[:size - dashLocation]

                            newDate = datetime.datetime.fromisoformat(strStart)

                            validDate = True

                            if Sd <= newDate <= Ed:
                                #print("in between S:" + str(Sd) + " DATE:" + str(start)+ " E:" + str(Ed) )
                                validDate = True
                            else:
                                print("### NOT DATE:" + str(start) + " NOT BETWEEN S:" + str(Sd) + " E:" + str(Ed) )
                                validDate = False

                        except ValueError:
                            print("### Unable to cast: " + start)
                            #For now let it pass!
                            validDate = True

                        if validDate:
                            time_date_event = start[0:10] + str(startTime) + opp

                            originalLocation = ""

                            try:
                                location = calendarGrabUtils.getMeetingLocationType(event["location"])
                                if location != "Remote":
                                    originalLocation = '"' + event["location"] + '"'
                                    location = "Onsite"
                            except ValueError:
                                location = "Remote"
                            except KeyError:
                                location = "Remote"
                            except:
                                location = "Remote"


                            if time_date_event not in time_date_event_list:
                                #The big write to the main file!
                                #fResults.write(start[0:10]+ ',' + 'START-' + str(startTime) + ',' + opp + ',' + eventSummary + ',' + eventType + ',' + str(meetingLength) + ',' + PDresponseStatus + ',' + CustomerAttended + '\n')
                                overallEventCount = overallEventCount + 1
                                SCeventCount = SCeventCount + 1
                                fResults.write(SCName + ',' + TeamName + ',' + start[0:10]+ ',' + 'START-' + str(startTime) + ',' + opp + ',' + eventType + ',' + str(meetingLength) + ',' + PDresponseStatus + ',' + CustomerAttended + ',IsRecurring:' + recurrence  + ',' + location.replace(",","") + ',' + originalLocation.replace(",","") + ',' + str(PDCount) + ',' + PDAttendees + '\n')
                                time_date_event_list.append(time_date_event)

                                ##### DEBUG PRINTING ######
                                print(SCName + ',' + TeamName + ',' + start[0:10] + ',' + 'START-' + str(startTime) + ',' + opp + ', EVENT:' + eventSummary + ',' + eventType + ',' + str(meetingLength) + ',' + 'START-' + str(startTime) + ',' + PDresponseStatus + ',' + CustomerAttended + ',IsRecurring:' + recurrence + ',' + location.replace(",","") + ',' + str(PDCount) + ',' + PDAttendees)
                                ################################################



            except KeyError as err:
                errCount = errCount + 1
                #print ('Cannot Get Event' + str(err))


        page_token = events.get('nextPageToken')
        if not page_token:
            break

    if SCeventCount > 0:
        print(str(eventCount) + ' events processed for ' + SCName + ' ' + str(SCeventCount) + ' customer events !')
    else:
        print(str(eventCount) + ' events processed for ' + SCName + ' - BUT NO CUSTOMER EVENTS!')
        cantReadSC = cantReadSC + ' ' + SCName

print('SC info capture complete - CUSTOMER EVENTS RECORDED = ' + str(overallEventCount) + ' Cannot capture events for ' + cantReadSC)
fDebug.close()
fResults.close()

