#imports
from flask import Flask, jsonify , request
from selenium import webdriver  
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from flask_cors import CORS
from selenium_stealth import stealth

chrome_driver_path = "/usr/local/bin/chromedriver"
chrome_bin_path = "/usr/bin/google-chrome"

from subprocess import run
print(run(["google-chrome-stable", "--version"], capture_output=True, text=True))

#PATH = "C:/Program Files (x86)/chromedriver.exe" 
options = Options()

options.binary_location = chrome_bin_path

options.add_argument('--lang=pt-BR')
options.add_argument('proxy-server="direct://"')
options.add_argument('proxy-bypass-list=*')

options.add_argument('--log-level=3')  # Suppress log level to show only severe errors
options.add_experimental_option('excludeSwitches', ['enable-logging'])

#options.add_experimental_option("detach", True) 

#Production Options
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
stealth(driver,
    languages=["pt-BR", "pt"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
    use_angle=True,
    passive_events=True,
    hide_browser_info=True
    )
driver.set_window_size(1920, 1080)
app = Flask(__name__)
CORS(app)

def check_exists_by_xpath(element, xpath):
    try:
        WebDriverWait(element, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except:
        return False

#define routes
@app.route('/')
def home():
    return "Hello World"

def scrape_car_data(cards, response, filters = None):
    for card in cards:
        try:
            WebDriverWait(card, 15).until(EC.presence_of_element_located((By.XPATH, ".//div[@class='total-amount_1XUQg1Kt']")))
        except TimeoutException:
            return driver.page_source
        price = card.find_element('xpath', ".//div[@class='total-amount_1XUQg1Kt']").text
        price = price.replace("R$ ","").replace(".","").replace(",",".")
        if filters and "max_price" in filters:
            if(float(price) > filters["max_price"]):
                continue
        try:
            company = WebDriverWait(card, 5).until(
                EC.presence_of_element_located((By.XPATH, ".//div[contains(@class, 'rental-company-evaluation-img')]//img"))
            ).get_attribute('alt').split(' ')[0]
        except TimeoutException:
            company = "Unknown"
        car_string = card.find_element('xpath', ".//div[contains(@class, 'card-vehicle-title')]").text
        modelo = car_string.split(' ')[1]
        marca = car_string.split(' ')[0]
        info = card.find_elements('xpath', ".//div[@class='booking-configurations']//ul//span")
        assentos = info[0].text
        cambio = info[2].text
        tipo = card.find_elements('xpath', ".//div[contains(@class, 'card-vehicle-title')]")[1].text.split(' ')[1]
        image = card.find_element('xpath', ".//div[contains(@class,'card-vehicle-container-left')]/img").get_attribute('src')
        if(check_exists_by_xpath(card, ".//div[contains(@class,'rental-company')]//img")):
            companyImage = card.find_element('xpath', ".//div[contains(@class,'rental-company')]//img")
            companyImage = companyImage.get_attribute('src')
        else:
            companyImage = ""
        response.append({
            "price" : price,
            "company" : company,
            "modelo" : modelo,
            "marca" : marca,
            "assentos" : assentos,
            "cambio" : cambio,
            "tipo" : tipo,
            "image" : image,
            "companyImage" : companyImage
        })
    return response

def scrape_hotel_data(cards, response, filters = None):
    for card in cards:
        images = []
        for image in card.find_elements('xpath', ".//img"):
            images.append(image.get_attribute('src'))
        price = card.find_elements('xpath', ".//div[@class='JGa7fd']")[0].text
        price = price.replace("R$ ","")
        if filters and "max_price" in filters:
            if(float(price) > filters["max_price"]):
                continue
        name = card.find_element('xpath', ".//div[@class='QT7m7']").text
        stars = ""
        if check_exists_by_xpath(card, ".//span[@class='KFi5wf lA0BZ ']"):
            stars = card.find_element('xpath', ".//span[@class='KFi5wf lA0BZ ']").text
            stars = stars.replace(",",".")
            if filters and "stars" in filters:
                if(float(stars) < filters["stars"]):
                    continue  
        reviews = ""
        if check_exists_by_xpath(card, ".//span[@class='jdzyld XLC8M ']"):
            reviews = card.find_element('xpath', ".//span[@class='jdzyld XLC8M ']").text
        characteristics = []
        for characteristic in card.find_elements('xpath', ".//div[@class='HlxIlc jBZYu']//span[2]"):
            characteristics.append(characteristic.text)
        check = False
        if filters and "services" in filters:
            for service in filters["services"]:
                if service in characteristics:
                    check = True
            if check == False:
                continue
        response.append({
            "name" : name,
            "image" : images,
            "stars" : stars,
            "reviews" : reviews,
            "characteristics" : characteristics,
            "price" : price
        })
    return response
        
def scrape_flight_data(cards, response, filters = None):
        for card in cards:
            if(check_exists_by_xpath(card, ".//div[contains(@class, 'YMlIz FpEdX')]//span")):
                price = card.find_element('xpath', ".//div[contains(@class, 'YMlIz FpEdX')]//span")
            else:
                price = driver.find_element('xpath', "//div[@class='QORQHb']/span")
            price = price.text.replace("R$ ","").replace(".","")
            if(price == ""):
                break
            if(filters and "max_price" in filters):
                if(float(price) > filters["max_price"]):
                    break
            if(filters and "min_price" in filters):
                if(float(price) < filters["min_price"]):
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
                if(float(stops) != filters["stops"]):
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
    typed = request.args.get('typed')
    driver.get("https://www.google.com/travel/flights?gl=BR&hl=pt-BR")
    driver.find_elements('xpath',"//input")[0].clear()
    driver.find_elements('xpath',"//input")[0].send_keys(typed)
    try:
        suggestions = WebDriverWait(driver,10).until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@class='DFGgtd']//li[@role='option']")))
    except TimeoutException:
        return driver.page_source
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
    travel_type = request.args.get('type') #ow(one-way) or rt(round-trip)
    infants_lap = request.args.get('infants_lap', type=int)
    children = request.args.get('children', type=int)
    infants_seat = request.args.get('infants_seat', type=int)
    adults = request.args.get('adults', type=int)
    travel_class = request.args.get('class') # economy, executive, first
    place_from = request.args.get('from')
    place_to = request.args.get('to')
    travel_departure = request.args.get('departure')
    travel_return = request.args.get('return')
    #travel_type = data['type'] #ow(one-way) or rt(round-trip)
    #infants_lap = data['infants_lap']
    #children = data['children'] 
    #infants_seat = data['infants_seat']
    #adults = data['adults']
    #travel_class =  data['class'] # economy, executive, first
    #place_from = data['from']
    #place_to = data['to']
    #travel_departure = data['departure']
    #travel_return = data['return']

    driver.get("https://www.google.com/travel/flights?gl=BR&hl=pt-BR")
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
    if(adults > 1 or (infants_seat + children + infants_lap) > 0):
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
    try:
        #WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'zISZ5c')]")))
        expand = driver.find_element('xpath', "//div[contains(@class, 'zISZ5c')]")
        expand.click()
        time.sleep(6)
    except NoSuchElementException:
        print("Não achou expandir")

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
    response = []
    response.append({"url" : driver.current_url})
    response = scrape_flight_data(driver.find_elements('xpath', "//div[@class='yR1fYc']"), response, filters)
    return jsonify(response)

    #price_slider -> //input[@class='VfPpkd-YCNiv']/
    
#running

@app.get("/hotels")
def hotels():
    place = request.args.get('place')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    adults = int(request.args.get('adults'))
    children = int(request.args.get('children'))
    driver.get('https://www.google.com/travel/search?q='+place+'&gl=BR&hl=pt-BR')
    inputs = driver.find_elements('xpath', "//div[@class='tbDMNe']//input")
    #Arrumar (Falta um focus pro enter funcionar (eu acho))
    #inputs[2].click()
    inputs[2].clear()
    inputs[2].send_keys(check_in)
    #inputs[3].click()
    time.sleep(1)
    inputs[3].clear()
    time.sleep(1)
    inputs[3].send_keys(check_out)
    
    if(adults != 2 or children > 0):
        time.sleep(2)
        people_div = driver.find_elements('xpath', "//div[@jsname='kj0dLd']")[1]
        time.sleep(1)
        people_div.click()
        time.sleep(0.5)
        passangers_buttons = driver.find_elements('xpath', "//div[@class='MlZqJf']//button") 
        if adults < 2:
            passangers_buttons[0].click()
        for _ in range(adults-2):
            passangers_buttons[1].click()
        for _ in range(children):
            passangers_buttons[3].click()
        driver.find_elements('xpath', "//div[@class='moeCJc']//button")[1].click()
        time.sleep(4)
        try:
            cards = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='uaTTDe BcKagd  bLc2Te Xr6b1e']")))
        except TimeoutException:
            return 0
        response = []
        response.append({"url" : driver.current_url})
        response = scrape_hotel_data(cards, response)
        return jsonify(response)
@app.get("/hotels/filter")
def apply_filter_hotel():
    driver.get(request.json['url'])
    time.sleep(1)
    filters = request.json['filters']
    #filtros: preço, avaliação, serviços
    response = []
    response.append({"url" : driver.current_url})
    try:
        cards = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='uaTTDe BcKagd  bLc2Te Xr6b1e']")))
    except TimeoutException:
        return 0
    response = scrape_hotel_data(cards , response, filters)
    return response
@app.get('/suggestion/cars')
def cars_suggestion():
    driver.get("https://www.rentcars.com/pt-br/")
    time.sleep(2)
    typed = request.args.get('typed')
    driver.find_element('xpath', "//div[@class='get-car-in']//input[@type='text']").send_keys(typed)
    try:
        suggestions = WebDriverWait(driver,3).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='get-car-in']//ul[contains(@class, 'autocomplete')]//li")))
    except TimeoutException:
        return 0
    response = []
    for suggestion in suggestions:
        tipo = 1 if "Cidades" in suggestion.get_attribute('aria-label') else 2
        response.append({"tipo" : tipo, "suggestion" : suggestion.find_elements('xpath', ".//span")[0].text})
    return jsonify(response)
@app.get("/teste")
def teste():
    driver.get('https://www.rentcars.com/pt-br/reserva/listar/201-1730206800-201-1730293200-0-0-0-0-0-0-0-0')
    time.sleep(4)
    try:
        return WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'rental-company-evaluation-img')]//img")))[0].get_attribute('alt')
    except TimeoutException:
        return 0

@app.get("/cars")
def cars():
    driver.get("https://www.rentcars.com/pt-br/")
    place = request.args.get('place')
    months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    data_retirada = request.args.get('data_retirada')
    data_devolucao = request.args.get('data_devolucao')
    data_retirada = data_retirada.split("-")
    data_devolucao = data_devolucao.split("-")
    time.sleep(2)
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='search-pickup-date elVal']"))
        )
    except TimeoutException:
        return driver.page_source
    driver.find_element('xpath', "//div[@class='search-pickup-date elVal']").click()
    time.sleep(1)
    month_selector_retirada = months[int(data_retirada[1])-1] + " " + data_retirada[0]
    retirada_found = False
    while not retirada_found:
        counter = 0
        for month in driver.find_elements('xpath', "//th[@class='month']"):
            if month.text == month_selector_retirada:
                retirada_found = True
                break 
            counter += 1
        if not retirada_found:
            driver.find_element('xpath', "//th[contains(@class, 'next')]//span").click()
        time.sleep(1)
    table_location = 'left' if counter == 0 else 'right'
    driver.find_element('xpath', "//div[@class='drp-calendar "+ table_location +"']//td//span[text()='"+str(int(data_retirada[2]))+"']").click()
    time.sleep(1)
    month_selector_devolucao = months[int(data_devolucao[1])-1] + " " + data_devolucao[0]
    devolucao_found = False
    while not devolucao_found:
        counter = 0
        for month in driver.find_elements('xpath', "//th[@class='month']"):
            if month.text == month_selector_devolucao:
                devolucao_found = True
                break 
            counter += 1
        if not devolucao_found:
            driver.find_element('xpath', "//th[contains(@class, 'next')]//span").click()
        time.sleep(1)
    table_location = 'left' if counter == 0 else 'right'
    driver.find_element('xpath', "//div[@class='drp-calendar "+ table_location +"']//td//span[text()='"+str(int(data_devolucao[2]))+"']").click()
    hora_retirada = request.args.get('hora_retirada')
    hora_devolucao = request.args.get('hora_devolucao')

    # Select the hour of pickup
    hora_retirada_select = driver.find_element('xpath', "//select[@id='HoraRetirada']")
    for option in hora_retirada_select.find_elements('tag name', 'option'):
        if option.text == hora_retirada:
            option.click()
            break

    # Select the hour of return
    hora_devolucao_select = driver.find_element('xpath', "//select[@id='HoraDevolucao']")
    for option in hora_devolucao_select.find_elements('tag name', 'option'):
        if option.text == hora_devolucao:
            option.click()
            break
    driver.find_element('xpath', "//div[@class='get-car-in']//input[@type='text']").send_keys(place)
    time.sleep(0.5)
    driver.find_element('xpath', "//div[@class='get-car-in']//input[@type='text']").send_keys(Keys.SPACE)
    time.sleep(3)
    driver.find_element('xpath', "//div[@class='get-car-in']//ul[contains(@class, 'autocomplete')]//li//span[1][contains(text(),'"+place+"')]").click()
    driver.find_element('xpath', "//div[@class='search-btn']//button").click()
    time.sleep(2)
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@rent-infinite-scroll-target]/div")))
    except TimeoutException:
        return jsonify({"error": "Timeout waiting for car data"}), 504
    time.sleep(1)
    cards = driver.find_elements('xpath', "//div[@rent-infinite-scroll-target]/div")
    response = []
    response.append({"url" : driver.current_url})
    response = scrape_car_data(cards, response)
    return jsonify(response)

@app.get("/attractions")
def attractions():
    place = request.args.get('place')
    driver.get("https://tourscanner.com/pt/search?q="+place)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//p[contains(text(), 'Atividades encontradas')]")))
    except TimeoutException:
        return jsonify({"error": "Timeout waiting for attractions"}, 504)
    
    cards = driver.find_elements('xpath', "//div[contains(@class,'flex-column w')]//ul//li")
    response = []
    for card in cards:
        try:
            card.find_element('xpath', ".//h2")
        except NoSuchElementException:
            return driver.page_source
        name = card.find_element('xpath', ".//h2").text
        image = card.find_element('xpath', ".//img").get_attribute('src')
        stars = card.find_elements('xpath', ".//div[@filled_stars]//span")[1].text
        reviews = card.find_elements('xpath', ".//div[@filled_stars]//span")[2].text
        try:
            price = card.find_element('xpath', ".//div[@class='flex items-end space-x-2']//div").text
        except NoSuchElementException:
            price = card.find_element('xpath', ".//div[@class='flex items-end space-x-2']//p").text
        price = price.replace("R$ ","")
        response.append({
            "name" : name,
            "image" : image,
            "stars" : stars,
            "reviews" : reviews,
            "price" : price
        })
    return jsonify(response)

if __name__ == "__main__":
    app.run()