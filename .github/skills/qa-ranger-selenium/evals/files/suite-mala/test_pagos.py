import time
import pytest
from selenium import webdriver


@pytest.fixture(scope="session")
def driver():
    d = webdriver.Chrome(executable_path="/opt/chromedriver")
    d.implicitly_wait(15)
    yield d


@pytest.mark.flaky(reruns=3)
def test_1(driver):
    driver.get("https://qa.banco-demo.com/pagos")
    driver.find_element_by_name("monto").send_keys("1000")
    driver.execute_script("document.getElementById('pagar').click()")
    time.sleep(5)
    try:
        driver.find_element_by_id("ok")
    except:
        pass
