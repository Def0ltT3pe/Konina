# parser_wb1.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_wb_price(url):
    try:
        # Настройка ChromeDriver
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument('--headless')  # Запуск без графического интерфейса

        # Запуск браузера
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        # Извлечение ID из URL (например, nm_id)
        product_id = url.split('/')[4]  # Предположим, что ID товара идет в URL после /catalog/

        # Извлечение наименования товара
        name = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-card-title"))
        ).text

        # Извлечение цены товара
        price = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "price-block__final-price"))
        ).text

        return {"product_id": product_id, "name": name, "price": price}

    except Exception as e:
        return {"error": f"Ошибка при извлечении данных: {e}"}

    finally:
        driver.quit()
