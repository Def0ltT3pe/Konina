from selenium import webdriver
from selenium.webdriver.firefox.service import Service

# Указываем полный путь к geckodriver.exe на вашем ПК.
service = Service("D:\Konina\geckodriver-v0.36.0-win64\geckodriver.exe")
driver = webdriver.Firefox(service=service)

# Открываем страницу Google
driver.get("http://www.google.com")

# Закрываем браузер после использования
driver.quit()