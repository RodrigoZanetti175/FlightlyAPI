#imports
from flask import Flask, jsonify , request
from selenium import webdriver  
import chromedriver_autoinstaller as chromedriver
import time
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


#PATH = "C:/Program Files (x86)/chromedriver.exe" 
chromedriver.install()
options = Options()
#options.add_experimental_option("detach", True) 
options.add_argument('--lang=pt-BR')
options.add_argument('--proxy-server="direct://"')
options.add_argument('--proxy-bypass-list=*')

options.add_argument('--log-level=3')  # Suppress log level to show only severe errors
options.add_experimental_option('excludeSwitches', ['enable-logging'])

driver = webdriver.Chrome(options=options)
driver.maximize_window()
app = Flask(__name__)

def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element('xpath', xpath)
    except NoSuchElementException:
        return False
    return True

#define routes
@app.route('/')
def home():
    return "ijfeuharhu"
def scrape_flight_data(cards, response, filters = None):
        for card in cards:
            if(check_exists_by_xpath(driver, ".//div[contains(@class, 'YMlIz FpEdX')]//span")):
                price = card.find_elements('xpath', ".//div[contains(@class, 'YMlIz FpEdX')]//span")[0]
            else:
                price = driver.find_element('xpath', "//div[@class='QORQHb']/span")
            price = price.text.replace("R$ ","").replace(".","")
            if(filters and "max_price" in filters):
                if(int(price) > filters["max_price"]):
                    break
            if(filters and "min_price" in filters):
                if(int(price) < filters["min_price"]):
                    continue
            travel_company = card.find_elements('xpath', ".//div[@class='sSHqwe tPgKwe ogfYpf']/span[not(@class)]")[0]
            travel_company = travel_company.text
            #maybe i'll have to check if filters["company"] exists instead of using in
            if(filters and "company" in filters):
                if(travel_company not in filters["company"]):
                    continue
            travel_time = card.find_elements('xpath', ".//span[@class='mv1WYe']//span[@role='text']")
            take_off = travel_time[0].text
            if(filters and "take_off" in filters):
                date_format = "%H:%M"
                if(datetime.strptime(take_off, date_format) > datetime.strptime(filters["take_off"],date_format)):
                    continue
            stops = card.find_element('xpath', ".//div[@class='EfT7Ae AdWm1c tPgKwe']//span[@class='ogfYpf']")
            stops = stops.text
            if(filters and "stops" in filters):
                if(int(stops) != filters["stops"]):
                    continue
            arrival = travel_time[1].text
            airports = card.find_elements('xpath', ".//div[@class='']")
            airport_from = airports[0].get_attribute('innerHTML')
            airport_to = airports[1].get_attribute('innerHTML')
            duration = card.find_element('xpath', ".//div[@class='gvkrdb AdWm1c tPgKwe ogfYpf']")
            duration = duration.text
            
            response.append({
                "take_off": take_off,
                "arrival": arrival,
                "company": travel_company,
                "price": price,
                "duration": duration,
                "airport_from": airport_from,
                "airport_to": airport_to,
                "stops": stops
                })
            
        return response
    
@app.get("/suggestion/flights/place")
def place():
    typed = request.json['typed']
    driver.get("https://www.google.com/travel/flights")
    driver.find_elements('xpath',"//input")[0].clear()
    driver.find_elements('xpath',"//input")[0].send_keys(typed)
    try:
        suggestions = WebDriverWait(driver,3).until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@class='DFGgtd']//li[@role='option']")))
    except TimeoutException:
        return 0
    response = []
    for suggestion in suggestions:
        #arrumar para o caso de não existir um specification ou acronym
        specification = None
        acronym = None
        
        suggestion_dict = {}
        suggestion_dict.update({"suggestion" : suggestion.find_element('xpath', ".//div[@class='zsRT0d']").get_attribute('innerHTML')})
        if(suggestion.find_elements('xpath', ".//div[@class='t7Thuc']")):
            specification = suggestion.find_element('xpath', ".//div[@class='t7Thuc']").get_attribute('innerHTML')
            specification = specification[:specification.find("<")]
            suggestion_dict.update({"specification" : specification})
        if(suggestion.find_elements('xpath', ".//div[@class='P1pPOe']")):
            suggestion_dict.update({"acronym" : suggestion.find_element('xpath', ".//div[@class='P1pPOe']").get_attribute('innerHTML')})
        suggestion_dict.update({"data-type" : suggestion.get_attribute('data-type')})
        response.append(suggestion_dict)
    
    return jsonify(response) 
   
@app.get("/flights")
def flights():
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
    time.sleep(6)
    cards = driver.find_elements('xpath', "//div[@class='yR1fYc']")
    
    response = []
    response.append({"url" : driver.current_url})
    response = scrape_flight_data(cards, response)
    return jsonify(response)

@app.get("/flights/return") #segunda fase -> recebe o indice do clique e o link da pagina que deve ser clicada
def phase2():
    driver.get(request.json['url'])
    time.sleep(2)
    response = []
    driver.find_elements('xpath', "//div[@class='yR1fYc']")[request.json['index']].click()
    time.sleep(2)
    response.append({"url" : driver.current_url})
    driver.find_element('xpath', "//div[contains(@class, 'zISZ5c')]").click()
    time.sleep(3)
    response = scrape_flight_data(driver.find_elements('xpath', "//div[@class='yR1fYc']"), response)
    return jsonify(response)
@app.get("/flights/summary") #terceira fase -> recebe o indice do clique e o link da pagina e retorna os dois voos escolhidos
def phase3():
    driver.get(request.json['url'])
    time.sleep(2)
    response = []
    driver.find_elements('xpath', "//div[@class='yR1fYc']")[request.json['index']].click()
    time.sleep(6) #Arrumar um jeito de esperar o site carregar completamente
    response.append({"url" : driver.current_url})
    #continuar
    cards = driver.find_elements('xpath', "//div[@role='list']/div") #cards da lista de voos
    response = scrape_flight_data(cards, response)
    others = [] #coleção de dicionarios
    reservations = driver.find_elements('xpath', "//div[@class='gN1nAc']") #cards de reserva
    for reservation in reservations:
        reservation_dict = {}
        reservation_dict.update({"price" : reservation.find_elements('xpath', ".//span")[0].text})
        reservation_dict.update({"company" : reservation.find_element('xpath', ".//div[@class='ogfYpf AdWm1c']").text})
        others.append(reservation_dict)
    response.append({"others" : others})
    return jsonify(response)
@app.get("/flights/redirect")
def redirect_flight():
    driver.get(request.json['url'])
    time.sleep(2)
    card = driver.find_elements('xpath', "//div[@class='gN1nAc']")[request.json['index']]
    card.find_element('xpath', ".//button").click()
    time.sleep(2)
    return driver.current_url
@app.get("/flights/filter")
def apply_filter():
    driver.get(request.json['url'])
    time.sleep(1)
    expand = driver.find_element('xpath', "//div[contains(@class, 'zISZ5c')]")
    expand.click()
    time.sleep(4)
    filters = request.json['filters']
    response = scrape_flight_data(driver.find_elements('xpath', "//div[@class='yR1fYc']"), [], filters)
    return jsonify(response)

    #price_slider -> //input[@class='VfPpkd-YCNiv']/
    
#running
@app.get("/hotels")
def hotels():
    place = request.json['place']
    check_in = request.json['check_in']
    check_out = request.json['check_out']
    driver.get('https://www.google.com/travel/search')
    inputs = driver.find_elements('xpath', "//div[@class='tbDMNe']//input")
    #Arrumar (Falta um focus pro enter funcionar (eu acho))
    inputs[0].clear()
    inputs[0].send_keys(place)
    time.sleep(1)
    inputs[0].send_keys(Keys.RETURN)
    #------------
    time.sleep(5)
    #inputs[2].click()
    inputs[2].clear()
    inputs[2].send_keys(check_in)
    #inputs[3].click()
    time.sleep(1)
    inputs[3].clear()
    time.sleep(1)
    inputs[3].send_keys(check_out)
    time.sleep(2)
    people_div = driver.find_elements('xpath', "//div[@jsname='kj0dLd']")[1]
    time.sleep(1)
    people_div.click()
    
    return "hello world"
if __name__ == "__main__":
    app.run()