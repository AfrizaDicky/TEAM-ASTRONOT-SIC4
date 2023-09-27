'''library'''
import time
import requests
import math
import RPi.GPIO as GPIO

SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
mq_in_dpin = 26
mq_in_apin = 0
mq_out_dpin = 16
mq_out_apin = 1
relay_in = 21
relay_out = 20
led_red = 19
led_green = 13


'''Memasukan variable dan token ubidots'''
TOKEN = "BBFF-emUBEbOePnS2723IwhFj2oOy3ZfdLO"  # Put your TOKEN here
DEVICE_LABEL = "astronot"  # Put your device label here 
VARIABLE_LABEL_1 = "persentase-co2"  # Put your first variable label here
VARIABLE_LABEL_2 = "kadar-co2"   # Put your second variable label here
VARIABLE_LABEL_3 = "persentase-o2"  # Put your third variable label here
VARIABLE_LABEL_4 = "kadar-o2"  # Put your forth variable label here
VARIABLE_LABEL_5 = "position"  # Put your fifth variable label here
VARIABLE_LABEL_6 = "kondisi-pompa-masuk"   # Put your six variable label here
VARIABLE_LABEL_7 = "kondisi-pompa-keluar"   # Put your seven variable label here


'''Fungsi init'''
def init():
         GPIO.setwarnings(False)
         GPIO.cleanup()#clean up at the end of your script
         GPIO.setmode(GPIO.BCM)#to specify whilch pin numbering system
         # set up the SPI interface pins
         GPIO.setup(SPIMOSI, GPIO.OUT)
         GPIO.setup(SPIMISO, GPIO.IN)
         GPIO.setup(SPICLK, GPIO.OUT)
         GPIO.setup(SPICS, GPIO.OUT)
         GPIO.setup(mq_in_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
         GPIO.setup(mq_out_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
         GPIO.setup(relay_in, GPIO.OUT)
         GPIO.setup(relay_out, GPIO.OUT)
         GPIO.setup(led_green, GPIO.OUT)
         GPIO.setup(led_red, GPIO.OUT)

'''read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)'''
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        ''' read in one empty bit, one null bit and 10 ADC bits'''
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout
    
'''read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)'''
def readadc_in(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcin = 1
       ''' read in one empty bit, one null bit and 10 ADC bits'''
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcin <<= 1
                if (GPIO.input(misopin)):
                        adcin |= 0x1

        GPIO.output(cspin, True)
        
        adcin >>= 1       # first bit is 'null' so drop it
        return adcin



'''Fungsi utama'''
def utama():
        init()
        print("please wait...")
        time.sleep(2)
        COlevel=readadc(mq_in_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
        O2level = readadc_in(mq_out_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
        persentase_co2 = round((COlevel/2047.)*100)
        persentase_o2 = round((O2level/4095.)*100)
        kadar_co2 = ((COlevel/2047.)*5)
        kadar_o2 = ((O2level/4095.)*5)
                        
        return persentase_co2,kadar_co2,persentase_o2,kadar_o2


'''Fungsi untuk pompa udara'''
def relay_udara_masuk():
    persentase_co2,kadar_co2,persentase_o2,kadar_o2 = utama()
    
    if persentase_co2 >=40:
        GPIO.output(relay_in, True)
         GPIO.output(led_green, True)
         GPIO.output(led_red, False)
        nilai_pompa_masuk = 1
        time.sleep(2)
        print("relay hidup")
    else:
        GPIO.output(relay_in, False)
         GPIO.output(led_red, True)
         GPIO.output(led_green, False)
        print("relay mati")
        nilai_pompa_masuk = 0
        
    return nilai_pompa_masuk

'''kontrol untuk relay fan'''
def relay_udara_keluar():
    persentase_co2,kadar_co2,persentase_o2,kadar_o2 = utama()
    
    if persentase_o2 <= 10:
        GPIO.output(relay_out, True)
        nilai_pompa_keluar = 1
        print("relay hidup keluar")
        time.sleep(2)
            
    else:
        GPIO.output(relay_out, False)
        nilai_pompa_keluar = 0
        print("relay mati")
            
    return nilai_pompa_keluar


'''Memasukan nilai untuk ubidots'''
def build_payload(variable_1, variable_2, variable_3, variable_4,variable_5,variable_6,variable_7):
    
    persentase_co2,kadar_co2,persentase_o2,kadar_o2 = utama()
    nilai_pompa_masuk = relay_udara_masuk()
    nilai_pompa_keluar = relay_udara_keluar()

    
    '''Creates six values for sending data'''
    print("kadar co2:", persentase_co2, "%")
    print(kadar_co2)
    print("kadar o2", persentase_o2, "%")
    print(kadar_o2)
    value_1 = persentase_co2
    value_2 = kadar_co2
    value_3 = persentase_o2
    value_4 = kadar_o2
    value_6 = nilai_pompa_masuk
    value_7 = nilai_pompa_keluar
    '''Creates a gps coordinates'''
    lat = -6.9907502
    lng = 110.4173773
    payload = {variable_1: value_1,
               variable_2: value_2,
               variable_3: value_3,
               variable_4: value_4,
               variable_5: {"value": 1, "context": {"lat": lat, "lng": lng}},
               variable_6: value_6,
               variable_7: value_7}

    return payload


'''Fungsi untuk request'''
def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

    '''Makes the HTTP requests'''
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.post(url=url, headers=headers, json=payload)
        status = req.status_code
        attempts += 1
        time.sleep(1)

    # Processes results
    print(req.status_code, req.json())
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False

    print("[INFO] request made properly, your device is updated")
    return True

'''Fungsi main loop'''
def main():
    payload = build_payload(
        VARIABLE_LABEL_1, VARIABLE_LABEL_2, VARIABLE_LABEL_3, VARIABLE_LABEL_4, VARIABLE_LABEL_5, VARIABLE_LABEL_6,VARIABLE_LABEL_7)

    print("[INFO] Attemping to send data")
    post_request(payload)
    print("[INFO] finished")


'''Fungsi untuk menjalankan program'''
if __name__ == '__main__':
    while (True):
        main()
        print("program continue")
        time.sleep(10)
