import csv
import json
import time

import grequests
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

'''
    APIs I used to fetch data:
        "shop_details_api": "https://shopee.vn/api/v4/shop/get_shop_detail?shopid={Shopee_ID}",
        "all_products_api": "https://shopee.vn/api/v4/shop/search_items?limit=100&shopid={Shopee_ID}&offset={offset}",
        "product_reviews_api": "https://shopee.vn/api/v2/item/get_ratings?itemid={itemid}&limit=59&offset={offset}&shopid={Shopee_ID}"
        
    To easy understand structure of json response, you can use https://jsonformatter.org/json-parser
'''

def config_driver():
    # options headless mode
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')

    # need to set user-agent to load all item, if not just got 42 instead of 60
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)
    
    return driver



def scroll_down_end_of_page(driver):
    '''
        Execute JS script for automate scroll down to the end to load full data of page.
    '''
    last_height = driver.execute_script('return document.body.scrollHeight')

    while True:
        driver.execute_script('window.scrollTo(0,  window.scrollY + 800);')
        time.sleep(0.5)
        new_height = driver.execute_script('return  window.scrollY + 800')
        if new_height == last_height:
            break
        last_height = new_height

    return driver

def scrape_shop_info(item_link):
    driver = config_driver()

    driver.get(item_link)
    time.sleep(5)
    english_btn = driver.find_element(by=By.XPATH, value='//*[@id="modal"]/div[1]/div[1]/div/div[3]/div[1]/button')
    english_btn.click()

    shop_name_locator = driver.find_element(by=By.CSS_SELECTOR, value='div[class="VlDReK"]')
    shop_name = shop_name_locator.text
    print(shop_name)
    driver.quit()



def dummy_func():
    ''' 
        dummy function to test and handle response on small data
    '''
    url = 'https://shopee.com.my/Hoodie-Men-Long-Sleeve-Baju-Lengan-Panjang-Sweatshirt-Man-Baju-T-Shirt-Lelaki-Lengan-Panjang-T-Shirt-Lengan-Panjang-Lelaki-M-3XL-i.134177481.19614535941?sp_atk=5c1db44c-a3e8-4102-82e5-ecbf79fb34ea&xptdk=5c1db44c-a3e8-4102-82e5-ecbf79fb34ea'
    # driver = config_driver()
    # driver.get(url=url)
    # soup = BeautifulSoup(driver.page_source, 'html.parser')
    # print(soup)

    # get shop_info by shop_id using API
    params = {
        'shopid': 134177481
    }
    shop_details_api = 'https://shopee.my/api/v4/shop/get_shop_detail'
    r = requests.get(shop_details_api, params=params)
    print(r.json())

def get_shop_ids():
    # list of urls category relevant to fashion, cosmetic.
    urls = [
        "https://shopee.com.my/Men-Clothes-cat.11000587",
        "https://shopee.com.my/Women-Clothes-cat.11000538",
        "https://shopee.com.my/Watches-cat.11001724",
        "https://shopee.com.my/Health-Beauty-cat.11000168",
        "https://shopee.com.my/Women-Shoes-cat.11000764",
        "https://shopee.com.my/Women's-Bags-cat.11000710",
        "https://shopee.com.my/Fashion-Accessories-cat.11000690",
        "https://shopee.com.my/Men's-Bags-Wallets-cat.11000745",
        "https://shopee.com.my/Muslim-Fashion-cat.11000616",
        "https://shopee.com.my/Men-Shoes-cat.11000781",
        "https://shopee.com.my/Travel-Luggage-cat.11000799",
    ]
    # start = time.time()
    total_shop_ids = set()
    driver = config_driver()

    for idx, url in enumerate(urls):
        print(url)
        driver.get(url=url)
        time.sleep(5)
        if idx == 0:
            english_btn = driver.find_element(by=By.XPATH, value='//*[@id="modal"]/div[1]/div[1]/div/div[3]/div[1]/button')
            english_btn.click()
        # find all item_link_locators
        '''
            example for item_link: 
            https://shopee.com.my/Hoodie-Men-Long-Sleeve-Baju-Lengan-Panjang-Sweatshirt-Man-Baju-T-Shirt-Lelaki-Lengan-Panjang-T-Shirt-Lengan-Panjang-Lelaki-M-3XL-i.134177481.19614535941?sp_atk=5c1db44c-a3e8-4102-82e5-ecbf79fb34ea&xptdk=5c1db44c-a3e8-4102-82e5-ecbf79fb34ea
            
            the '-i.134177481.19614535941' in item link stands for '-i.{shop_id}.{item_id}'
        '''
        # get total pages of category
        category_pages_locator = driver.find_element(by=By.CSS_SELECTOR, value='span[class="shopee-mini-page-controller__total"]')
        pages = int(category_pages_locator.text)

        for page in range(0,pages):
            url = f'{urls[0]}?page={page}'
            if page != 0:
                driver.get(url=url)
                time.sleep(5)
            driver = scroll_down_end_of_page(driver=driver)
            
            item_link_locators = driver.find_elements(by=By.CSS_SELECTOR, value='a[data-sqe="link"]')
            item_links = [item_link_locator.get_attribute('href') for item_link_locator in item_link_locators]

            # get shop_ids from item_links
            print(item_links[0].split('-i.')[1].split('.')[0])

            # this list contains all shop_ids includes duplicate
            shop_ids_dups = list(item_link.split('-i.')[1].split('.')[0] for item_link in item_links)
            # print(len(shop_ids_dups))

            # use set to store list to implicit not add duplicate shop_id
            total_shop_ids.update(shop_ids_dups)
        print(len(total_shop_ids))

    # write data into a file  
    with open('shop_ids.csv', 'w') as f:
        writer = csv.writer(f)

        writer.writerow(['shop_id'])
        for shop_id in total_shop_ids:
            writer.writerow([shop_id])
    # end = time.time()
    # print(f"Time taken for normal scraper: {end - start} seconds")

def get_shop_detail_from_shop_id():
    ''' 
        Get shop_detail from shop_id using shop_details_api

        get more shop_info data use requests slower than grequests
        time taken on ~700 shops/requests
        requests: >5 mins 
        grequests: 10 secs :))

    - This is normal way using requests:
        for shop_id in shop_ids:
            print(shop_ids.index(shop_id))
            params = {
                'shopid': int(shop_id)
            }
            shop_details_api = 'https://shopee.my/api/v4/shop/get_shop_detail'
            r = requests.get(shop_details_api, params=params)
            data = r.json()['data']
            shop_name = data['account']['username']
            shop_item_count = data['item_count']
            shop_url = f'{BASE_URL}{shop_name}'

            shop_names.append(shop_name)
            shop_item_counts.append(shop_item_count)
            shop_urls.append(shop_url)   
   '''
    # read shop_ids from file
    shop_ids = []
    with open('shop_ids.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        shop_ids = [row[0] for row in csv_reader]

    BASE_URL = 'https://shopee.com.my/'
    shop_names = []
    shop_item_counts = []
    shop_urls = []
 
    # Use grequests to fetch data from api
    # start = time.time()
    shop_detail_apis = [f'https://shopee.my/api/v4/shop/get_shop_detail?shopid={shop_id}' for shop_id in shop_ids]
    reqs = [grequests.get(url) for url in shop_detail_apis]
    resps = grequests.map(reqs)
    for resp in resps:
        data = json.loads(resp.text)['data']
        shop_name = data['account']['username']
        shop_item_count = data['item_count']
        shop_url = f'{BASE_URL}{shop_name}'

        shop_names.append(shop_name)
        shop_item_counts.append(shop_item_count)
        shop_urls.append(shop_url)
    
    header = ['shop_id', 'shop_name', 'shop_item_count', 'shop_url']

    # write data into a file  
    with open('shop_info_greq.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(header)

        writer.writerows(zip(shop_ids, shop_names, shop_item_counts, shop_urls))
    # end = time.time()
    # print(f"Time taken for grequest scraper: {end - start} seconds")

def get_product_detail_from_shop_id():
    '''
        In normal way of using requests module,
        Send one request, take the response, transform, load data into a list and loop this process one by one
        Then write list to a file

        By using grequests module,
        Its send multiple requests at one time, and then for each response return, I do the same process to storage data

        Total requests send: 3143 (requests) on 700 shops
        Time taken of grequests: ~250 secs for 272K records - thats kind a huge performance.

        start = time.time()
        for shop_id in shop_ids:
            offset = 0
            limit = 100
            while True:
                params = {
                    'limit': 100,
                    'shopid': shop_id,
                    'offset': offset
                }
                all_products_api = 'https://shopee.my/api/v4/shop/search_items'
                r = requests.get(all_products_api, params=params)
                data = r.json()
                total_item_nums = data['total_count']
                print(total_item_nums)
                item_nums = len(data['items'])
                for i in range(item_nums):
                    item_id = data['items'][i]['itemid']
                    item_name = data['items'][i]['item_basic']['name']
                    item_image = ','.join(data['items'][i]['item_basic']['images'])
                    item_price =  data['items'][i]['item_basic']['price'] / 100000
                    item_url = f'{BASE_URL}{item_name.replace(" ", "-") + f"-i.{shop_id}.{item_id}"}'
                    
                    item_names.append(item_name)
                    item_images.append(item_image)
                    item_prices.append(item_prices)
                    item_urls.append(item_urls)
                # print(total_item_nums, item_nums, item_id, item_name, item_image, item_price, item_url, sep='\n')
                if offset < total_item_nums:
                    if offset + limit >= total_item_nums:
                        break
                    else: 
                        offset += limit
        print(len(item_names))
        end = time.time()
        print(f"Time taken for requests scraper: {end - start} seconds")
    '''
    
    shop_ids = []
    shop_item_counts = [] # use this for grequests, otherwise remove it
    with open('shop_info_greq.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            shop_ids.append(row[0])
            shop_item_counts.append(int(row[2])) # use this for grequests, otherwise remove it
    
    BASE_URL = 'https://shopee.com.my/'
    # BASE_IMG_URL = 'https://cf.shopee.com.my/file/'
    item_ids = []
    item_names = []
    item_images = []
    item_prices = []
    item_urls = []

    # Using grequests to fetch data from api
    # start = time.time()        
    all_products_apis = []
    for shop_id in shop_ids:
        idx = shop_ids.index(shop_id)
        offset = 0
        limit = 100
        while True:
            all_products_apis.append(f'https://shopee.my/api/v4/shop/search_items?limit={limit}&shopid={shop_id}&offset={offset}')
            if offset < shop_item_counts[idx]:
                if offset + limit >= shop_item_counts[idx]:
                    break
                else: 
                    offset += limit

    reqs = (grequests.get(url, timeout=5) for url in all_products_apis)
    resps = grequests.imap(reqs, size=10)

    for resp in resps:
        try:
            data = json.loads(resp.text)
            if data['total_count'] == 0:
                print(f'no more even offset less than total')
            else:
                item_nums = len(data['items'])
                print(item_nums)
                # print(data['total_count'])
                for i in range(item_nums):
                    item_id = data['items'][i]['itemid']
                    shop_id = data['items'][i]['shopid']
                    item_name = data['items'][i]['item_basic']['name']
                    item_image = ','.join(data['items'][i]['item_basic']['images'])
                    item_price =  data['items'][i]['item_basic']['price'] / 100000
                    item_url = f'{BASE_URL}{item_name.replace(" ", "-") + f"-i.{shop_id}.{item_id}"}'
                    
                    item_ids.append(item_id)
                    item_names.append(item_name)
                    item_images.append(item_image)
                    item_prices.append(item_price)
                    item_urls.append(item_url)
        except:
            print(f'request failed: {resp}')
    # end = time.time()
    # print(f"Time taken for requests scraper: {end - start} seconds")
    
    # write data into a file  
    header = ['item_id, item_name', 'item_image', 'item_price', 'item_url']
    with open('product_info_greq.csv', 'a') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(header)

        writer.writerows(zip(item_ids, item_names, item_images, item_prices, item_urls))
        
if __name__ == '__main__':
    get_shop_ids()
    get_shop_detail_from_shop_id()
    get_product_detail_from_shop_id()
