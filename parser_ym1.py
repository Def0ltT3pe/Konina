from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
import re


def extract_sku_and_product_id(url: str):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    sku = query_params.get('sku', [None])[0]
    match = re.search(r'/product--[^/]+/(\d+)', parsed_url.path)
    product_id = match.group(1) if match else None

    # Преобразуем product_id в int, если он найден
    product_id = int(product_id) if product_id and product_id.isdigit() else None

    return sku, product_id


def get_ym_data(sku: str, product_id: int):
    options = webdriver.FirefoxOptions()
    # options.add_argument('--headless')  # Включи, если не хочешь видеть браузер
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'
    )
    options.set_preference('dom.webdriver.enabled', False)
    options.set_preference('useAutomationExtension', False)
    options.set_preference('intl.accept_languages', 'ru-RU,ru')

    driver = None
    try:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        url = f"https://market.yandex.ru/product/{product_id}?sku={sku}"
        driver.get(url)

        result = {
            "nm_id": int(sku) if sku.isdigit() else None,  # Преобразуем nm_id в int
            "name": None,
            "price": None,
        }

        # Увеличиваем время ожидания
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Проверка на страницу ошибки
        error_elems = driver.find_elements(By.CSS_SELECTOR, 'div[class*="error"], div[class*="not-found"]')
        for elem in error_elems:
            if "не найден" in elem.text.lower() or "ошибка" in elem.text.lower():
                result["name"] = "Ошибка: Товар не найден"
                return result

        # Название товара
        try:
            name_elem = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    'h1[data-additional-zone="title"], h1[data-auto="productCardTitle"], h1'
                ))
            )
            result["name"] = name_elem.text.strip()
        except Exception:
            result["name"] = "Ошибка: Название не найдено"

        # Цена товара (с использованием нового селектора для цены)
        try:
            price_elem = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    'span.ds-text.ds-text_weight_bold.ds-text_color_price-term'
                ))
            )
            price_text = price_elem.text.strip()
            print(f"Цена, найденная на странице: {price_text}")  # Для отладки

            # Очистка от всех пробелов и ненужных символов
            price_digits = re.sub(r'[^\d]', '', price_text)  # Убираем все, кроме цифр
            result["price"] = float(price_digits) if price_digits else None
        except Exception as e:
            print(f"Ошибка при извлечении цены: {str(e)}")  # Для отладки
            result["price"] = "Ошибка: Цена не найдена"

        return result

    except Exception as e:
        return {"nm_id": int(sku) if sku.isdigit() else None, "name": f"Ошибка: {str(e)}", "price": None}
    finally:
        if driver:
            driver.quit()


# === Точка входа ===
if __name__ == "__main__":
    url = "https://market.yandex.ru/product--watch-pro-2/861347316?sku=103757197929&uniqueId=164019620&do-waremd5=7MWQCXC44b4uZevVEyURLA"

    sku, product_id = extract_sku_and_product_id(url)

    if sku and product_id:
        data = get_ym_data(sku, product_id)
        print("Результат парсинга:")
        print(data)
    else:
        print("Ошибка: Не удалось извлечь sku или product_id")
