import selenium #Selenium with Python is used to carry out automated test cases for browsers or web applications
import time
import schedule
from selenium import webdriver #Webdriver is the parent of all methods and classes used in Selenium Python
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

path="C:/Users/Name/OneDrive/Desktop/Chromedriver.exe" #Path to browser driver (Chrome)
driver=webdriver.Chrome(path) #Get path
driver.get("https://charts.bogged.finance/?token=0x8076C74C5e3F5852037F31Ff0093Eeb8c8ADd8D3") #Chart websites with wanted crypto coins

driver.execute_script("window.open('https://poocoin.app/tokens/0x82eb29d3eb0719af341f6b18c0d9d749c0cd16b6');") #Open crypto coin in new tab (MarsMission.finance (MARSM/BNB))
driver.execute_script("window.open('https://poocoin.app/tokens/0xce5814efff15d53efd8025b9f2006d4d7d640b9b');") #Open crypto coin in new tab (Moonstar (MOONSTAR/BNB))
driver.execute_script("window.open('https://poocoin.app/tokens/0x2a9718deff471f3bb91fa0eceab14154f150a385');") #Open crypto coin in new tab (ElonGate (ElonGate/BNB))
driver.execute_script("window.open('https://poocoin.app/tokens/0xa8fcee78b782ef97380326e90df80d72f025f020');") #Open crypto coin in new tab (TacoCat (TACOCAT/BNB))

driver.set_window_size(1024, 600) #Resize chrome window
driver.maximize_window()


