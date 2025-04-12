from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_wb_price(nm_id):
    try:
        # Настройка ChromeDriver
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument('--headless')  # Запуск без графического интерфейса

        # Запуск браузера
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx")

        # Ждём загрузки цены (макс. 15 секунд)
        price = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "price-block__final-price"))
        ).text
        return price
    except Exception as e:
        return f"Ошибка: {e}"
    finally:
        driver.quit()
