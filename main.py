import sched
import time
import pyttsx3
import json
from flask import Flask, render_template, request, redirect
from uk_covid19 import Cov19API
import requests 
import datetime
import logging
from datetime import datetime

#setting the configerations for the logging function
logging.basicConfig(filename='ca3.log', level=logging.DEBUG, format= '%(asctime)s: %(levelname)s :%(funcName)s :%(message)s')

#setting all global variables
covid_list = []
news = []
my_dict = {}
weather_dict = {}
weather_list = {}
w_list = []
notif = []
notif_deleted = []
alarm_deleted = []
display_alarm_list = []
display_list = []
display_list1 = []
alarm_list = []
new_covid_cases = {'new': 0}
engine = pyttsx3.init()
s = sched.scheduler(time.time, time.sleep)

#get_api to get all information from the config file
def get_api():
    try:
        f = open('config.json')
        logging.info("config.json file successfully opened")
    except:
        logging.warning("config.json file failed to open")
        pass
    global api_config
    api_config = json.load(f)
    return(api_config)


#get the filtered data from the covid 19 api
def get_covid():
    my_dict.clear()
    covid_list.clear()
    #setting the filters according to the config file
    england_only = [
        'areaType=%s' % api_config['covid_areaType'],
        'areaName=%s' % api_config['covid_areaName']
    ]

    cases_and_deaths = {
        "date": "date",
        "areaName": "areaName",
        "newCasesByPublishDate": "newCasesByPublishDate",
        "cumCasesByPublishDate": "cumCasesByPublishDate",
        "newDeathsByDeathDate": "newDeathsByDeathDate",
    }

    api = Cov19API(filters=england_only, structure=cases_and_deaths, latest_by='date') 
    try:
        data = api.get_json()
        logging.info("covid api successfully retrieved")
    except:
        data = []
        logging.warning("covid api failed to work")
    data = data['data'][0]
    #setting the title and content of the covid data to be displayed on the html template
    my_dict['title'] = "Covid 19 Daily Report"
    new_deaths = str(data['newDeathsByDeathDate'])
    #changing the value of new deaths to no if there are no new deaths
    if new_deaths == 'None':
        new_deaths = "no"
    my_dict['content'] = "Today there are " + str(data['newCasesByPublishDate']) + " new cases, " + str(new_deaths) + " new deaths, "  + str(data['cumCasesByPublishDate']) + " total cases."
    # display is used to tell if the data should be displayed in notifcations and hasnt been deleted, alarm is the same for the alarm display section
    my_dict['display'] = "yes"
    my_dict['alarm'] = "no"
    #new cases is used to check if it has passed the threshold inputted by the user
    my_dict['new_cases'] = data['newCasesByPublishDate']
    #taking the covid data dict and putting it into a list for easier use when attaching news weather and covid into 1 list later on
    covid_list.append(my_dict)
    logging.info("returning covid_list")
    return(covid_list)

def get_news():
    news.clear()
    base_url = api_config['news_url']
    api_key = api_config['news_api_key']
    country = api_config['news_country']
    complete_url = base_url + "country=" + country + "&apiKey=" + api_key
    try:
        response = requests.get(complete_url)
        logging.info("news api successfully retrieved")
    except:
        response = []
        logging.warning("news api failed to work")
    x = response.json()
    y = x['articles']
    #checking if the covid filter that the user inputs through the config file has been apllied
    if api_config['news_covid_filter'] == "yes":
        #checking for key words in the title of each article to see if they relate to covid
        for i in range(len(y)):
            new_dict = {}
            if "COVID" in y[i]['title'] or "Covid" in y[i]['title'] or "vaccine" in y[i]['title'] or "VACCINE" in y[i]['title'] or "pandemic" in y[i]['title'] or "PANDEMIC" in y[i]['title']:
                new_dict['title'] = str(y[i]['title'])
                new_dict['content'] = str(y[i]['description']) + " " + str(y[i]['url'])
                new_dict['display'] = "yes"
                new_dict['alarm'] = "no"
                news.append(new_dict)
    #if they have not applied the filter then the desired into is put into a dictionary and added to a list
    else:
        for i in range(len(y)):
            new_dict = {}
            new_dict['title'] = str(y[i]['title'])
            new_dict['content'] = str(y[i]['description']) + " " + str(y[i]['url'])
            new_dict['display'] = "yes"
            new_dict['alarm'] = "no"
            news.append(new_dict)

    logging.info("returning news")
    return(news)

def get_weather():  
    weather_list.clear()
    w_list.clear()
    api_url = "http://api.openweathermap.org/data/2.5/weather?q="
    api_key = api_config['weather_api_key']
    api_location = api_config['weather_api_location']
    api_unit = api_config['weather_api_measurement']

    api = api_url + api_location + "&units=" + api_unit + "&appid=" +api_key
    try:
        response = requests.get(api)
        logging.info("weather api successfully retrieved")
    except:
        logging.warning("weather api failed to work")
        response = {}
    weather_data = response.json()
    desc = weather_data['weather']
    desc = desc[0]['description']
    temp1 = weather_data['main']
    temp1.pop('pressure')
    wind = weather_data['wind']
    wind.pop('deg')
    #taking all desired values and putting it into 1 string to be read displayed or read out later
    a = desc
    b = str(wind['speed'])
    c = str(temp1['temp'])
    d = str(temp1['feels_like'])
    e = str(temp1['temp_min'])
    f = str(temp1['temp_max'])
    g = str(temp1['humidity'])

    content = "the forecast for today is " + a + " with temperatures of " + c + " degrees celcius but feels like " + d + " with highs of " + f + " degrees, and lows of " + e + " degrees. the humidity is " + g + " percent and the wind speed is " + b + " kilometers per hour "

    weather_list['title'] = "Daily weather"
    weather_list['content'] = content
    weather_list['display'] = "yes"
    weather_list['alarm'] = "no"
    w_list.append(weather_list)
    logging.info("returning w_list")

    return(w_list)

def get_alarms(alarm_time, label_alarm):
    #this function takes the label and time of a set alarm and puts it into a list of dictioanrys to be displayed under alarms
    alarm_dict = {}
    alarm_dict['title'] = label_alarm
    alarm_dict['content'] = "This alarm is going off at " + alarm_time[11:13] + ":" + alarm_time[14:] + " " + alarm_time[8:10] + "/" + alarm_time[5:7] + "/" + alarm_time[0:4]
    alarm_dict['alarm'] = "yes"
    try:
        alarm_list.append(alarm_dict)
        logging.info("alarm_list successfully appended alarm_dict")
    except:
        logging.warning("alarm_list failed to append alarm_dict")
        pass

    return(alarm_list)

def alarm_set(datetimeObj):
    #this function takes the time set by the user and returns the delay for the alarm in seconds
    now = datetime.now()
    time_to_alarm = datetimeObj - now
    delay_alarm = time_to_alarm.total_seconds()
    return(delay_alarm)


def remove():
    #this function removes the deleted notification 
    notif_deleted.append(request.args.get('notif'))
    logging.info("%s added to notif_deleted" % request.args.get('notif'))
    return(notif_deleted)

def remove_alarm():
    #this function removes the deleted alarm 
    alarm_deleted.append(request.args.get('alarm_item'))
    logging.info("%s added to alarm_deleted" % request.args.get('alarm_item'))


def combine_notif():
    #this function combines all the lists from the covid, news and weather into a singular list to be displayed
    notif.clear()
    display_list.clear()
    try:
        #allways inserting so the covid data apears at the top, then the weather, then the news in notifcations
        notif.extend(news)
        notif.insert(0, weather_list)
        notif.insert(0, my_dict)
        logging.info("news weather and covid successfully inserted into notif")
    except:
        logging.warning("news weather and covid failed to inserted into notif")
        pass
    #checking to see if the notifaction has already been deleted from the notifcations so it wont display it again
    for i in notif:
        if i['title'] in notif_deleted:
            logging.info("found %s in notif_deleted" % i['title'])
            i['display'] = "no" 
            i['alarm'] = "no"
    #checking if the notifcation should be displayed and if so is added to the display list
    for i in notif:
        if i['display'] == "yes":
            display_list.append(i)


def combine_alarm():
    #same as combine notif but for the alarms
    display_alarm_list.clear()

    #checking if the alarm has already been deleted and if so doesnt display it
    for i in alarm_list:
        if i['title'] in alarm_deleted:
            logging.info("found %s in alarm_deleted" % i['title'])
            i['alarm'] = "no"
    for i in alarm_list:
        if i['alarm'] == "yes":
            #if the alarm can be displayed, it is added to the alarm display list
            display_alarm_list.append(i)

def announce_weather(announcement, label_alarm):
    #this function is to annouce for only weather alarms

    #checks if the alarm has already been deleted and if not will annouce it
    if label_alarm not in alarm_deleted:
        try:
            engine.endLoop()
            logging.info("engine.endloop successfull")
        except:
            pass
        #putting the label and the content of the annoucement into 1 string to all be read out
        # the, , , , is used to create a small pause imbetween speaking the label and the content
        a = label_alarm + ", , , ," + announcement
        engine.say(a)
        engine.runAndWait()
        logging.info("weather alarm has gone off")
        #after speaking, the alarm is added to the deleted list so it wont display or be read out again
        alarm_deleted.append(label_alarm)
    

def announce_news(announcement, label_alarm):
    #this function annouces alarms for only news

    #checks if the alarm has already been deleted
    if label_alarm not in alarm_deleted:
        read = label_alarm
        i = 0 
        for i in range(len(news)):
            #checks if the news article has already been deleted and wont read it out if so
            if news[i]['title'] not in notif_deleted:
                #adds the label from before with the news titles into 1 string to be read out
                read = read + ", , , , , , ,      ," + news[i]['title'] + ", , , , , , ,      ,"
            i = i + 1
        
        try:
            engine.endLoop()
            logging.info("engine.endloop successfull")
        except:
            pass
        engine.say(read)
        engine.runAndWait()
        logging.info("news announcement successfull")
        #after speaking, the alarm is added to the deleted list so it wont display or be read out again
        alarm_deleted.append(label_alarm)


def announce_alarm(announcement):
    #this function is for alarms that are not news or weather

    #first checks if the alarm has been deleted
    if announcement not in alarm_deleted:
        try:
            engine.endLoop()
            logging.info("engine.endloop successfull")
        except:
            pass
        engine.say(announcement)
        engine.runAndWait()
        logging.info("standered alarm announcement successfull")
        #after speaking, the alarm is added to the deleted list so it wont display or be read out again
        alarm_deleted.append(announcement)

def announce_weather_news(label_alarm, weather_info, news):
    #this function is to read out alarms for both news and weather at the same time
    if label_alarm not in alarm_deleted:
        a = label_alarm + ", , , ," + weather_info
        #adds the label, weather and news into 1 string to be read out
        i = 0 
        for i in range(len(news)):
            if news[i]['title'] not in notif_deleted:
                a = a + ", , , , , , ,      ," + news[i]['title'] + ", , , , , , ,      ,"
            i = i + 1

        try:
            engine.endLoop()
            logging.info("engine.endloop successfull")
        except:
            pass
        engine.say(a)
        engine.runAndWait()
        logging.info("news and weather announcement succesful")
        #after speaking, the alarm is added to the deleted list so it wont display or be read out again
        alarm_deleted.append(label_alarm)

def covid_check_threshold(new_covid_cases):
    #checks if the new covid cases is greater than the users threshold and if so will read it out
    a = int(new_covid_cases['new'])
    #checking whether the covid cases have changed and if so will check if it has passed the threshold
    if int(my_dict['new_cases']) != a:
        a = int(my_dict['new_cases'])
        if a > int(api_config['covid_threshold']):
            logging.info("new cases are greater than the threshold")
            #adds the info into a 1 string to be read out
            say = "Today's new cases have passed the threshold of " + api_config['covid_threshold'] + " with " + str(a) + " cases"
            try:
                engine.endLoop()
                logging.info("engine.endloop successfull")
            except:
                pass
            engine.say(say)
            engine.runAndWait()
            logging.info("covid threshold announcement succesfull")
    return(a)    



app = Flask(__name__)

@app.route('/')
@app.route('/index')
def program_run():
    s.run(blocking=False)
    #assigning any imput to a variable
    weather_get = request.args.get('weather')
    news_get = request.args.get('news')
    alarm_time = request.args.get('alarm')
    label_alarm = request.args.get('two')
    
    #calling the functions
    get_api()
    get_weather()
    get_news()
    get_covid()

    #checking if an alarm has been set
    if alarm_time:
        #changing the alarm format into a datetime formate to calculate the delay
        datetimeObj = datetime.strptime(alarm_time, '%Y-%m-%dT%H:%M')
        if datetimeObj > datetime.now():
            #get the delay
            delay_alarm = alarm_set(datetimeObj)
            #set the alarm onto the alarm notifaction
            get_alarms(alarm_time, label_alarm)

            #checking if weather, news, weather and news or nether have been selected to make the correct alarm
            if weather_get == "weather" and news_get == None:
                logging.info("weather only alarm set, %s" %label_alarm)
                #setting the alarm
                s.enter(int(delay_alarm), 1, announce_weather, [weather_list['content'],label_alarm])
            if news_get == "news" and weather_get == None:
                logging.info("news only alarm set, %s" %label_alarm)
                #setting the alarm
                s.enter(int(delay_alarm), 2, announce_news, [news, label_alarm])
            if weather_get == None and news_get == None:
                logging.info("standered alarm set, %s" %label_alarm)
                #setting the alarm
                s.enter(int(delay_alarm), 3, announce_alarm, [label_alarm,])
            if weather_get == "weather" and news_get == "news":
                logging.info("weather and news alarm set, %s" %label_alarm)
                #setting the alarm
                s.enter(int(delay_alarm), 3, announce_weather_news, [label_alarm, weather_list['content'], news])
            
    #checking if the user wants to delete a notifaction
    if request.args.get('notif'):
        logging.info("%s requested to be removed from notifcations" % request.args.get('notif'))
        remove()
    
    #checking if the user wants to delete an alarm
    if request.args.get('alarm_item'):
        logging.info("%s requested to be removed from alarms" % request.args.get('alarm_item'))
        remove_alarm()

    #combining the alarms and notifcations anf checking the threshold
    combine_alarm()
    combine_notif()
    updated_covid = covid_check_threshold(new_covid_cases)
    new_covid_cases['new'] = updated_covid

    #rendering the template with the display lists, title and image
    return render_template("template.html", title = "Daily update", notifications = display_list, alarms = display_alarm_list, image='clock.jpg')

if __name__ == '__main__':
    app.run()
