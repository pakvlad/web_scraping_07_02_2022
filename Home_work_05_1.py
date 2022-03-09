import time
import unicodedata
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime
from random import randint

from urllib.parse import urljoin
from pymongo import MongoClient

MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_DB = "VK_POSTS"
MONGO_COLLECTION = "posts"


def insert_only_new(data_post):
    with MongoClient(MONGO_HOST, MONGO_PORT) as client:
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        collection.update_one(
            {'id_post': data_post['id_post']},
            {'$set': data_post,
             '$currentDate': {'lastModified': True}},
            upsert=True,
        )
    return True


DRIVER_PATH = "./selenium_driver/chromedriver.exe"

url = "https://vk.com/tokyofashion"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(DRIVER_PATH, options=options)
driver.get(url)

time.sleep(2)
search_btn = driver.find_element_by_xpath("//a[contains(@class, 'ui_tab_search')]")
search_btn.click()
time.sleep(3)
text_search = 'tokyo'
search_input = driver.find_element_by_xpath('//input[@class="ui_search_field _field"]')
print(search_input)
time.sleep(3)
search_input.send_keys(text_search + '\n')
time.sleep(5)


def check_box_layout(driver):
    try:
        find_box_layout = driver.find_element_by_xpath('//div[@class="box_layout"]')
        time.sleep(2)
        not_now_link = driver.find_element_by_xpath('//a[@class="JoinForm__notNowLink"]').click()
        return True
    except Exception:
        return False


check_box_layout(driver)


def data_from_bs(html_el):
    try:
        result_dict = {}
        soup_post = BeautifulSoup(html_el, "lxml")
        element = soup_post.find('span', attrs={'class': 'rel_date'})
        result_dict['date_post'] = unicodedata.normalize("NFKD", element.text) if element else None
        element = soup_post.find('div', attrs={'class': 'wall_post_text'})
        result_dict['text_post'] = element.text if element else None
        element = soup_post.find('div')
        result_dict['id_post'] = element['data-post-id'] if element else None
        result_dict['href_post'] = urljoin(url, '?w=wall' + element['data-post-id']) if element else None
        element = soup_post.find('div', attrs={'class': 'PostButtonReactions__title _counter_anim_container'})
        result_dict['likes_count'] = element.text if element else None
        element = soup_post.find('div', attrs={'class': 'PostBottomAction PostBottomAction--withBg share _share'})
        result_dict['repost_count'] = element['data-count'] if element else None
        element = soup_post.find('div', attrs={'class': 'like_views like_views--inActionPanel'})
        result_dict['view_count'] = element['title'].split(' ')[0] if element else None
        return result_dict
    except Exception:
        return None


list_posts = []
start_post = 0
posts_count = 0
last_height = 0
while True:
    posts = driver.find_elements_by_xpath("//div[contains(@id, 'post-')]")
    posts_count = len(posts)
    for post in posts[start_post:posts_count]:
        outer_html = post.get_attribute("outerHTML")
        post_data = data_from_bs(outer_html)
        if post_data:
            insert_only_new(post_data)
        else:
            print('Ошибка при парсинге ', outer_html[150])
    start_post = max(0, posts_count - 30)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(randint(5, 8))
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height
    check_box_layout(driver)
print('Сбор данных завершен')