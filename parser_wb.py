from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_wb_data(nm_id: str):
    # Настройка Selenium с Firefox
    options = webdriver.FirefoxOptions()
    # Для тестов можно отключить headless
    # options.add_argument('--headless')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'
    )
    # Дополнительные опции для обхода детекции
    options.set_preference('dom.webdriver.enabled', False)
    options.set_preference('useAutomationExtension', False)

    driver = None
    try:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        url = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"
        logger.info(f"Открытие URL: {url}")
        driver.get(url)

        # Инициализация результата
        result = {
            "nm_id": nm_id,
            "name": None,
            "price": None,
        }

        # Проверка загрузки страницы
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Проверка на страницу ошибки
        error_elems = driver.find_elements(By.CSS_SELECTOR, '.error-page, h1, div[class*="error"]')
        for elem in error_elems:
            if "не найден" in elem.text.lower() or "ошибка" in elem.text.lower():
                result["name"] = "Ошибка: Товар не найден"
                logger.warning(f"Товар не найден для nm_id={nm_id}")
                return result

        # Название товара
        try:
            name_elem = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'h1[class*="product-page__title"], h1'))
            )
            result["name"] = name_elem.text.strip()
            logger.info(f"Название найдено: {result['name']}")
        except Exception as e:
            result["name"] = f"Ошибка: Название не найдено: {str(e)}"
            logger.error(f"Ошибка при поиске названия: {str(e)}")

        # Цена товара
        try:
            price_elem = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'ins.price-block__final-price'))
            )
            price_text = price_elem.text.strip()
            result["price"] = price_text.replace('₽', '').replace('\xa0', '').strip()
            logger.info(f"Цена найдена: {result['price']}")
        except Exception as e:
            result["price"] = f"Ошибка: Цена не найдена: {str(e)}"
            logger.error(f"Ошибка при поиске цены: {str(e)}")

        return result

    except Exception as e:
        logger.error(f"Общая ошибка для nm_id={nm_id}: {str(e)}")
        return {"nm_id": nm_id, "name": f"Ошибка: {str(e)}", "price": None}
    finally:
        if driver:
            driver.quit()
            logger.debug("Браузер закрыт")

# Пример использования
if __name__ == "__main__":
    nm_id = "133281680"
    data = get_wb_data(nm_id)
    print(data)