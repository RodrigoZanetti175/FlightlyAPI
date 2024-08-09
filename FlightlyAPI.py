#imports
from flask import Flask
from flask import request
from selenium import webdriver  
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


#setup
PATH = "C:/Program Files (x86)/chromedriver.exe" 
options = Options()
options.add_experimental_option("detach", True) 
driver = webdriver.Chrome(service=Service(PATH), options=options)
driver.maximize_window()
app = Flask(__name__)

#define routes
@app.route('/')
def home():
    return "ijfeuharhu"
@app.route("/flights", methods=['GET', 'POST'])
def flights():
    if request.method == 'POST':
        travel_type = request.json['type'] #ow(one-way) or rt(round-trip)
        infants_lap = request.json['infants_lap']
        children = request.json['children'] 
        infants_seat = request.json['infants_seat']
        adults = request.json['adults']
        travel_class =  request.json['class'] # economy, executive, first
        place_from = request.json['from']
        place_to = request.json['to']
        travel_departure = request.json['departure']
        travel_return = request.json['return']

        driver.get("https://www.google.com/travel/flights")

        time.sleep(1)
        inputs = driver.find_elements('xpath', "//input")
        inputs[2].send_keys(place_to)
        time.sleep(1)
        local = driver.find_element('xpath', "//ul[@class='DFGgtd']//li//div[@class='zsRT0d'][text()='"+place_to+"']")
        local.click()
        time.sleep(1)
        inputs[0].click()
        time.sleep(1)
        inputs[1].clear()
        time.sleep(1)
        inputs[1].send_keys(place_from)
        time.sleep(1)
        local = driver.find_element('xpath', "//ul[@class='DFGgtd']//li//div[@class='zsRT0d'][text()='"+place_from+"']")
        local.click()
        time.sleep(1)
        inputs[4].click()
        time.sleep(1)
        inputs[6].send_keys(travel_departure)
        #setting travel type
        if travel_type == 'rt':
            time.sleep(1)
            inputs[7].click()
            inputs[7].send_keys(travel_return)
            inputs[7].send_keys(Keys.ENTER)
            inputs[7].send_keys(Keys.ENTER)
        else:
            travel_type_selector = driver.find_elements('xpath', "//div[@class='VfPpkd-aPP78e']")[0]
            travel_type_selector.click()
            time.sleep(0.5)
            travel_type_button = driver.find_elements('xpath', "//ul[contains(@class, 'VfPpkd-rymPhb')]//li")[1]
            travel_type_button.click()

        time.sleep(1)

        #setting passangers
        if(adults > 1 or sum(infants_seat, children, infants_lap) > 0):
            passangers_selector = driver.find_elements('xpath', "//button[contains(@class,'VfPpkd-LgbsSe')]")[8]
            passangers_selector.click()
            time.sleep(0.5)
            passangers_buttons = driver.find_elements('xpath', "//ul[@class='Xdzhob Lxea9c']//button") 
            for i in range(adults-1):
                passangers_buttons[1].click()
            for i in range(children):
                passangers_buttons[3].click()
            for i in range(infants_seat):
                passangers_buttons[5].click()
            for i in range(infants_lap):
                passangers_buttons[7].click()
            
            passangers_buttons[3].send_keys(Keys.ESCAPE)
        time.sleep(0.5)
        if(travel_class != "economy"):
            travel_class_selector = driver.find_elements('xpath', "//div[@class='VfPpkd-aPP78e']")[1]
            travel_class_selector.click()
            travel_class_button = driver.find_elements('xpath', "//ul[contains(@class,'VfPpkd-rymPhb')]//li")
            for button in travel_class_button:
                if travel_class in button.get_attribute("innerHTML"):
                    button.click()
        time.sleep(1)
        search_button = driver.find_element('xpath', "//div[@class='MXvFbd']//button[contains(@class, 'VfPpkd-LgbsSe')]")
        search_button.click()
        time.sleep(1)
        #start scrapping
        expand = driver.find_element('xpath', "//div[contains(@class, 'zISZ5c')]")
        expand.click()
        time.sleep(2.5)
        cards = driver.find_elements('xpath', "//div[@class='yR1fYc']")
        json = "{\n"
        i = 0
        for card in cards:
            travel_time = card.find_elements('xpath', ".//span[@class='mv1WYe']//span[@role='text']")
            take_off = travel_time[0].text
            arrival = travel_time[1].text
            travel_company = card.find_elements('xpath', ".//div[@class='sSHqwe tPgKwe ogfYpf']/span[not(@class)]")[0]
            travel_company = travel_company.text
            airports = card.find_elements('xpath', ".//div[@class='']")
            airport_from = airports[0].get_attribute('innerHTML')
            airport_to = airports[1].get_attribute('innerHTML')
            duration = card.find_element('xpath', ".//div[@class='gvkrdb AdWm1c tPgKwe ogfYpf']")
            duration = duration.text
            stops = card.find_element('xpath', ".//div[@class='EfT7Ae AdWm1c tPgKwe']//span[@class='ogfYpf']")
            stops = stops.text
            price = card.find_elements('xpath', ".//div[contains(@class, 'YMlIz FpEdX')]//span")[0]
            price = price.text
            json += '{'
            json += '"take_off":"' + take_off + '",'
            json += '"arrival":"' + arrival + '",'
            json += '"company":"'+ travel_company + '",'
            json += '"price":"'+ price + '",'
            json += '"duration":"'+ duration + '",'
            json += '"airport_from":"'+ airport_from + '",'
            json += '"airport_to":"'+ airport_to + '",'
            json += '"stops":"'+ stops + '"'
            json += '},'
        
        json += "}"
    return json
   
#running
@app.route("/hotels", methods=['GET', 'POST'])
def hotels():
    if request.method == 'POST':
        place = request.json['place']
        check_in = request.json['check_in']
        check_out = request.json['check_out']

        driver.get('https://www.google.com/travel/search')

        inputs = driver.find_elements('xpath', "//div[@class='tbDMNe']//input")
        time.sleep(1)
        inputs[0].clear()
        time.sleep(1)
        inputs[0].send_keys(place)
        time.sleep(1)
        #inputs[2].click()
        inputs[2].clear()
        inputs[2].send_keys(check_in)
        #inputs[3].click()
        time.sleep(1)
        inputs[3].clear()
        inputs[3].send_keys(check_out)
        
        return "hello world"
if __name__ == "__main__":
    app.run()







