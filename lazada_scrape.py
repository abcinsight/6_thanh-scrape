import csv
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

'''
    APIs I used to fetch data:
        "shop_details_api": "https://shopee.vn/api/v4/shop/get_shop_detail?shopid={Shopee_ID}",
        "all_products_api": "https://shopee.vn/api/v4/shop/search_items?limit=100&shopid={Shopee_ID}&offset={offset}",
        "product_reviews_api": "https://shopee.vn/api/v2/item/get_ratings?itemid={itemid}&limit=59&offset={offset}&shopid={Shopee_ID}"
'''


def config_driver():
    # options headless mode
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')

    # need to set user-agent to load all item, if not just got 42 instead of 60
    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)

    return driver

def get_shop_ids_lazada():
    '''
        all_products_of_shop https://www.lazada.com.my/lomogi-official-store/?q=All-Products&from=wangpu&langFlag=en'
        seller_name = data['mods']['listItems'][idx]['sellerName']
        seller_id = data['mods']['listItems'][idx]['sellerId']
        shop_id = data['mods']['listItems'][idx]
        shop_url = f'{BASE_URL}{shop_name.lower().replace(' ', '-')}'
    '''
    BASE_URL = 'https://www.lazada.com.my/'

    seller_ids = []
    shop_ids = []
    shop_names = []
    shop_urls = []

    # get max_pages of category
    # url = 'https://www.lazada.com.my/shop-women-dresses/'
    # driver = config_driver()
    # driver.get(url)
    # time.sleep(5)
    # pages = driver.find_element(by=By.CSS_SELECTOR, value='ul[class="ant-pagination"]')
    # max_page = int(pages.find_elements(by=By.CSS_SELECTOR, value='li')[-2].get_attribute('title'))

    datas = []
    prev_data = []
    new_data = []
    page = 1
    while True:
        print(page)
        url = f'https://www.lazada.com.my/shop-women-dresses/?ajax=true&isFirstRequest=true&page={page}'
        r = requests.get(url, headers={
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'referer': url
        })
        data = r.json()
        new_data = prev_data
        datas.append(data)
        if page % 20 == 0:
            time.sleep(0.7)
        item_nums = len(data['mods']['listItems'])
        print(item_nums)
        for i in range(item_nums):
            seller_id = data['mods']['listItems'][i]['sellerId']

            shop_id = data['mods']['listItems'][i]['clickTrace'].split(':')[-1]
            shop_name = data['mods']['listItems'][i]['sellerName']
            shop_url = f'{BASE_URL}{shop_name.lower().replace(" ", "-")}'
            seller_ids.append(seller_id)
            shop_ids.append(shop_id)
            shop_names.append(shop_name)
            shop_urls.append(shop_url)
        page += 1
        if prev_data == new_data:
            break
        else:
            prev_data = new_data
            new_data = []
            page += 1
    header = ['seller_id', 'shop_id', 'shop_name', 'shop_url']
    with open('shop_info_lazada_req_unique.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(header)

        writer.writerows(zip(seller_ids, shop_ids, shop_names, shop_urls))


def get_product_detail_from_shop_id_lazada():
    shop_ids = []
    shop_urls = []
    with open('shop_info_lazada_req_unique.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            shop_ids.append(row[1])
            shop_urls.append(row[3])

    BASE_URL = 'https://www.lazada.com.my/'

    header = ['shop_id', 'item_id', 'item_name',
              'item_image', 'item_price', 'item_url']
    with open('product_info_lazada_1.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)

    # 154
    for i, shop_url in enumerate(shop_urls):
        page = 1
        print(page)

        item_shop_ids = []
        item_ids = []
        item_names = []
        item_images = []
        item_prices = []
        item_urls = []

        prev_data = []
        new_data = []
        while True:
            print(i)
            all_product_shop_url = f'{shop_url}/?q=All-Products&from=wangpu&langFlag=en&pageTypeId=2&isFirstRequest=true&ajax=true&page={page}'
            headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
                'referer': all_product_shop_url
            }
            try:
                r = requests.get(all_product_shop_url,headers=headers)
                time.sleep(3)
                data = r.json()
                # item_id, item_name, item_image, item_price, item_url
                item_nums = len(data['mods']['listItems'])
                for idx in range(item_nums):
                    item_id = data['mods']['listItems'][idx]['nid']
                    item_name = data['mods']['listItems'][idx]['name']
                    item_price = data['mods']['listItems'][idx]['price']

                    image_nums = len(data['mods']['listItems'][idx]['thumbs'])
                    item_image_lst = []
                    for jdx in range(image_nums):
                        item_image_lst.append(
                            data['mods']['listItems'][idx]['thumbs'][jdx]['image'])
                        item_image = ','.join(item_image_lst)
                        item_images.append(item_image)
                    item_url = data['mods']['listItems'][idx]['itemUrl'][2:]
                    new_data.append(item_id)
                    if item_id not in item_ids:
                        item_ids.append(item_id)
                        item_names.append(item_name)
                        item_prices.append(item_price)
                        item_urls.append(item_url)
                        item_shop_ids.append(shop_ids[i])
                time.sleep(2)
                
            except Exception as e:
                print(e)
            if prev_data == new_data:
                break
            else:
                prev_data = new_data
                new_data = []
                page += 1
        with open('product_info_lazada_1.csv', 'a') as csv_file:
                writer = csv.writer(csv_file)

                writer.writerows(zip(item_shop_ids, item_ids, item_names,
                                item_images, item_prices, item_urls))

if __name__ == '__main__':
    get_shop_ids_lazada()
    get_product_detail_from_shop_id_lazada()