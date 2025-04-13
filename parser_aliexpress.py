from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs
import re

def get_aliexpress_data(url: str):
    service = Service("C:\\Users\\svobo\\Documents\\GitHub\\Konina\\geckodriver-v0.36.0-win64\\geckodriver.exe")
    options = webdriver.FirefoxOptions()
    #options.add_argument('--headless')

    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)

    # Парсим URL и получаем sku_id, если есть
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    sku_id = query_params.get('sku_id', [None])[0]

    # Если sku_id не найден, ищем его в исходном коде страницы
    if not sku_id:
        try:
            page_source = driver.page_source
            match = re.search(r'"skuId"\s*:\s*"(\d+)"', page_source)
            if match:
                sku_id = match.group(1)
        except:
            sku_id = "0"

    # Имя товара
    try:
        name = driver.find_element(By.CSS_SELECTOR, 'h1.snow-ali-kit_Typography__base__1shggo').text
    except Exception as e:
        name = f"Ошибка: {e}"

    # Цена
    try:
        price_text = driver.find_element(By.CSS_SELECTOR, '.HazeProductPrice_SnowPrice__mainS__1wzo3').text
        price = price_text.replace('₽', '').replace('\xa0', '').replace(' ', '')
    except Exception as e:
        price = f"Ошибка: {e}"

    driver.quit()

    return {
        "sku_id": sku_id,
        "name": name,
        "price": price,
        "marketplace": "Aliexpress"
    }
if __name__ == "__main__":
    url = "https://aliexpress.ru/item/1005008216442145.html?spm=a2g2w.home.10009201.3.6f135586Ue6SPj&mixer_rcmd_bucket_id=aerabtestalgoRecommendAbV2_testRankingTimLialikov&ru_algo_pv_id=672037-55914f-9d1519-9725ba-1744534800&scenario=aerAppJustForYouNewRuSellTab&sku_id=12000044268637948&traffic_source=recommendation&type_rcmd=core"
    data = get_aliexpress_data(url)
    print(data)
