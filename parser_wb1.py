from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


def get_wb_price(nm_id: str):
    # Формируем URL на основе nm_id
    url = f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx"

    # Настройка Firefox WebDriver
    service = Service("D:\\Konina\\geckodriver-v0.36.0-win64\\geckodriver.exe")  # Обрати внимание: слэши правильные
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')

    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get(url)

        # Получаем название товара
        try:
        # .product-page__title
        # name = driver.find_element(By.CSS_SELECTOR, 'h1.goods-name').text
            name = driver.find_element(By.CLASS_NAME, 'product-page__title').text
        except Exception as e:
            name = f"Ошибка при получении названия: {str(e)}"

        # Получаем цену товара

        try:
            price = driver.find_element(By.CLASS_NAME, 'price-block__final-price').text
            # Очищаем цену от лишних символов
            price = price.replace('₽', '').replace('\xa0', '').strip()
        except Exception as e:
            price = f"Ошибка при получении цены: {str(e)}"

        return {
            "nm_id": nm_id,
            "name": name,
            "price": price
        }

    except Exception as e:
        return {
            "nm_id": nm_id,
            "error": f"Ошибка при обработке страницы: {str(e)}"
        }
    finally:
        driver.quit()

print(get_wb_price("369971388"))