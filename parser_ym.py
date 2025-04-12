from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_ym_data(sku: str, product_id: str):
    options = webdriver.FirefoxOptions()
    # options.add_argument('--headless')  # Раскомментировать для продакшена
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'
    )
    options.set_preference('dom.webdriver.enabled', False)
    options.set_preference('useAutomationExtension', False)
    options.set_preference('intl.accept_languages', 'ru-RU,ru')  # Русская локаль

    driver = None
    try:
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        url = f"https://market.yandex.ru/product/{product_id}?sku={sku}"
        driver.get(url)

        result = {
            "nm_id": sku,
            "name": None,
            "price": None,
        }

        WebDriverWait(driver, 15).until(
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
            name_elem = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR,
                    'h1[data-additional-zone="title"], h1[data-auto="productCardTitle"], h1'
                ))
            )
            result["name"] = name_elem.text.strip()
        except Exception:
            result["name"] = "Ошибка: Название не найдено"

        # Цена товара
        try:
            price_elem = WebDriverWait(driver, 15).until(
                EC.visibility_of_any_elements_located((
                    By.CSS_SELECTOR,
                    'span.ds-text.ds-text_weight_bold.ds-text_color_price-term.ds-text_typography_headline-3.ds-text_headline-3_tight.ds-text_headline-3_bold, span[data-auto="mainPrice"], span[class*="_price_"], div[class*="offer-price"] span'
                ))
            )[0]
            price_text = price_elem.text.strip()
            result["price"] = price_text.replace('₽', '').replace('\xa0', '').strip()
        except Exception:
            result["price"] = "Ошибка: Цена не найдена"

        return result

    except Exception as e:
        return {"nm_id": sku, "name": f"Ошибка: {str(e)}", "price": None}
    finally:
        if driver:
            driver.quit()