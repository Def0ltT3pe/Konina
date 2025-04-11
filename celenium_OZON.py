from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

# Укажите путь к geckodriver
service = Service("D:\Konina\geckodriver-v0.36.0-win64\geckodriver.exe")  # Замените на фактический путь к geckodriver
driver = webdriver.Firefox(service=service)

# Откройте страницу товара
url = 'https://aliexpress.ru/item/1005007900377783.html?sku_id=12000042770116010&spm=a2g2w.productlist.search_results.0.2857c34eMhO5sH'  # Замените на URL товара
driver.get(url)

# Найдите элемент с ценой
try:
    price_element = driver.find_element(By.CSS_SELECTOR, '.l3z_28')
    price = price_element.text
    print(f'Цена товара: {price}')
except Exception as e:
    print(f'Ошибка: {e}')

# Закройте браузер
driver.quit()