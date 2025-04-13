from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import re
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_nm_id_from_url(url: str):
    """
    Извлекает nm_id из URL Wildberries.
    Пример URL: https://www.wildberries.ru/catalog/133281680/detail.aspx
    """
    match = re.search(r'/catalog/(\d+)/detail.aspx', url)
    if match:
        return match.group(1)
    return None

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
            "nm_id": int(nm_id),  # Преобразуем nm_id в int
            "name": None,
            "price": None,
            "marketplace":"Wildberries"
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
            # Убираем ₽, пробелы и заменяем на float
            result["price"] = float(price_text.replace('₽', '').replace('\xa0', '').replace(' ', ''))
            logger.info(f"Цена найдена: {result['price']}")
        except Exception as e:
            result["price"] = f"Ошибка: Цена не найдена: {str(e)}"
            logger.error(f"Ошибка при поиске цены: {str(e)}")
        # Получение URL изображения
        try:
            image_elem = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'img[data-link*="photo-slider"]'))
            )
            result["image"] = image_elem.get_attribute("src")
            logger.info(f"Изображение найдено: {result['image']}")
        except Exception as e:
            result["image"] = None
            logger.warning(f"Не удалось получить изображение: {str(e)}")

        return result

    except Exception as e:
        logger.error(f"Общая ошибка для nm_id={nm_id}: {str(e)}")
        return {"nm_id": int(nm_id), "name": f"Ошибка: {str(e)}", "price": None}
    finally:
        if driver:
            driver.quit()
            logger.debug("Браузер закрыт")

# Пример использования
if __name__ == "__main__":
    url = "https://www.wildberries.ru/catalog/133281680/detail.aspx"  # Пример URL

    # Извлекаем nm_id из URL
    nm_id = extract_nm_id_from_url(url)

    if nm_id:
        data = get_wb_data(nm_id)
        print(data)
    else:
        print("Ошибка: Не удалось извлечь nm_id из URL")
