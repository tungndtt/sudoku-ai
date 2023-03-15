import os
import json
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DATA_DIRS = "./data"
urls = {
    "easy": "https://sudoku.tagesspiegel.de/sudoku-leicht/",
    "normal": "https://sudoku.tagesspiegel.de/",
    "hard": "https://sudoku.tagesspiegel.de/sudoku-schwer/",
    "extreme": "https://sudoku.tagesspiegel.de/sudoku-sehr-schwer/"
}


def checkDir(dirs):
    if not os.path.exists(dirs):
        os.makedirs(dirs)


def crawlData(args):
    (src, num_samples) = args
    url = urls[src]
    driver = webdriver.Chrome()
    driver.get(url)
    driver.maximize_window()
    timeout = 10
    iframe = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, "//iframe[@title='Iframe title']"))
    )
    driver.switch_to.frame(iframe)
    accept_btn = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, "//button[@title='Alle akzeptieren']"))
    )
    accept_btn.click()
    driver.switch_to.default_content()
    start_btn = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='sudoku-start-btn']"))
    )
    start_btn.click()
    table_xpath = "//table[@class='sudoku']"
    driver.execute_script(
        "arguments[0].scrollIntoView();",
        driver.find_element(By.XPATH, table_xpath)
    )

    data_dirs = f"{DATA_DIRS}/{src}"
    checkDir(data_dirs)
    data_file = f"{data_dirs}/data.json"
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            samples = json.load(f)
    else:
        samples = {"data": [], "labels": []}
    num_existing_data = len(samples["labels"])
    try:
        for i in range(num_existing_data, num_existing_data + num_samples):
            label_vector = []
            rows = driver.find_elements(By.XPATH, table_xpath + "//tr")
            assert len(rows) == 9
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                assert len(cells) == 9
                for cell in cells:
                    cell_value = cell.text
                    if cell_value:
                        cell_value = int(cell_value)
                    else:
                        cell_value = 0
                    label_vector.append(cell_value)
            
            file_name = f"{data_dirs}/{i}.png"
            samples["data"].append(file_name)
            samples["labels"].append(label_vector)
            driver.find_element(By.XPATH, table_xpath).screenshot(file_name)
            driver.find_element(By.XPATH, "//button[text()='Neues Spiel']").click()
            start_btn = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[@class='sudoku-start-btn']"))
            )
            start_btn.click()
    finally:
        driver.quit()
        with open(data_file, "w+") as f:
            json.dump(samples, f, indent=2)


checkDir(DATA_DIRS)
NUM_SAMPLES = 10
params = [(src, NUM_SAMPLES) for src in urls.keys()]
with concurrent.futures.ThreadPoolExecutor(max_workers=len(params)) as executor:
    executor.map(crawlData, params)
