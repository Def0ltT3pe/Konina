from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs

def get_aliexpress_data(url: str):
    # Укажите путь к geckodriver
    service = Service("D:\\Konina\\geckodriver-v0.36.0-win64\\geckodriver.exe")  # Обрати внимание: слэши правильные
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')  # Без интерфейса

    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)

    # Парсим URL и получаем sku_id
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    sku_id = query_params.get('sku_id', [None])[0]

    # Имя товара
    try:
        name = driver.find_element(By.CSS_SELECTOR, 'h1.snow-ali-kit_Typography__base__1shggo').text
    except Exception as e:
        name = f"Ошибка: {e}"

    # Цена
    try:
        price_text = driver.find_element(By.CSS_SELECTOR, '.HazeProductPrice_SnowPrice__mainS__1wzo3').text
        price = price_text.replace('₽', '').replace('\xa0', '').strip()
    except Exception as e:
        price = f"Ошибка: {e}"

    driver.quit()

    return {
        "sku_id": sku_id,
        "name": name,
        "price": price
    }


