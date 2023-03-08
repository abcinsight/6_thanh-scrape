import csv
import json
import os
import time
import grequests
from datetime import datetime
'''
    APIs I used to fetch data:
        "shop_details_api": "https://shopee.my/api/v4/shop/get_shop_detail?shopid={Shopee_ID}",
        "all_products_api": "https://shopee.my/api/v4/shop/search_items?limit=100&shopid={Shopee_ID}&offset={offset}",
        "product_reviews_api": "https://shopee.my/api/v2/item/get_ratings?itemid={itemid}&limit=59&offset={offset}&shopid={Shopee_ID}"
        "shop_by_category_api": "https://shopee.com.my/api/v4/official_shop/get_shops_by_category?need_zhuyin=0&category_id={category_id}"
        "shop_base_detail_api": "https://shopee.com.my/api/v4/shop/get_shop_base?entry_point=&username={shop_username}&version=1"
    
    To easy understand structure of json response, you can use https://jsonformatter.org/json-parser
'''

def get_data_from_urls(urls):
    reqs = (grequests.get(url) for url in urls)
    resps = grequests.map(reqs, size=50)
    return resps

def get_shopee_mall_basic_info():

    # all category_id relevant to fashion, cosmetic
    category_ids = [
        11000587,
        11000538,
        11001724,
        11000168,
        11000764,
        11000710,
        11000690,
        11000745,
        11000616,
        11000781,
    ]
    BASE_URL = 'https://shopee.com.my/'
    total_shop = 0
    shop_ids = []
    shop_logos = []
    shop_names = []
    shop_usernames = []
    shop_urls = []

    shops_by_category_urls = [f'https://shopee.com.my/api/v4/official_shop/get_shops_by_category?need_zhuyin=0&category_id={category_id}' for category_id in category_ids]
    resps = get_data_from_urls(shops_by_category_urls)
    
    for resp in resps:
        data = json.loads(resp.text)['data']
        total_shop += data['brand_count']
        for brand in data['brands']:
            for shop_info in brand['brand_ids']:
                shop_id = shop_info['shopid']
                shop_logo = shop_info['logo']
                shop_username = shop_info['username']
                shop_name = shop_info['brand_name']
                shop_url = f'{BASE_URL}{shop_username}'

                if shop_id not in shop_ids:
                    shop_ids.append(shop_id)
                    shop_logos.append(shop_logo)
                    shop_usernames.append(shop_username)
                    shop_names.append(shop_name)
                    shop_urls.append(shop_url)

    print(f'total_shop_from_api: {total_shop} \ntotal_shop_no_duplicate: {len(shop_ids)}')

    header = ['shop_id', 'shop_logo', 'shop_name', 'shop_username', 'shop_url']

    with open('shopee_mall_basic_info.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(header)

        writer.writerows(zip(shop_ids, shop_logos, shop_names, shop_usernames, shop_urls))
    

def get_shopee_mall_detail_from_shop_id():
   
    start = time.time()
    shop_ids = []
    shop_logos = []
    shop_names = []
    shop_usernames = []
    shop_urls = []
    with open('shopee_mall_basic_info.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            shop_ids.append(row[0])
            shop_logos.append(row[1])
            shop_names.append(row[2])
            shop_usernames.append(row[3])
            shop_urls.append(row[4])
    

    shop_ratings = []
    shop_item_counts = []
    shop_follower_counts = []
    shop_descriptions = []
    
    shop_detail_urls = [f'https://shopee.com.my/api/v4/shop/get_shop_detail?shopid={shop_id}' for shop_id in shop_ids]
    
    resps = get_data_from_urls(shop_detail_urls)
    for resp in resps:
        data = json.loads(resp.text)['data']
        shop_rating = data.get('rating_star', None)
        shop_item_count = data['item_count']
        shop_follower_count = data['follower_count']
        shop_description = data.get('description', None)
        
        shop_ratings.append(shop_rating)
        shop_item_counts.append(shop_item_count)
        shop_follower_counts.append(shop_follower_count)
        shop_descriptions.append(shop_description)

        
    header = ['shop_id', 'shop_logo', 'shop_name', 'shop_username', 'shop_url', 'shop_rating', 'shop_item_count', 'shop_follower_count', 'shop_description']
    with open('shopee_mall_detail_info.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(header)

        writer.writerows(zip(shop_ids, shop_logos, shop_names, shop_usernames, shop_urls, shop_ratings, shop_item_counts, shop_follower_counts, shop_descriptions))
    end = time.time()
    print(f"Time taken for scraper: {end - start} seconds")

def get_shopee_mall_product_from_shop_id():
    shop_ids = []
    shop_item_counts = []  # use this for grequests, otherwise remove it
    with open('shopee_mall_detail_info.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            shop_ids.append(row[0])
            # use this for grequests, otherwise remove it
            shop_item_counts.append(int(row[6]))

    BASE_URL = 'https://shopee.com.my/'
    # BASE_IMG_URL = 'https://cf.shopee.com.my/file/'
    product_shop_ids = []
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
            all_products_apis.append(
                f'https://shopee.my/api/v4/shop/search_items?limit={limit}&shopid={shop_id}&offset={offset}')
            if offset <= shop_item_counts[idx]:
                if offset + limit >= shop_item_counts[idx]:
                    break
                else:
                    offset += limit
    print(len(all_products_apis))
    reqs = (grequests.get(url) for url in all_products_apis)
    resps = grequests.imap(reqs, size=50)

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
                    item_image = ','.join(
                        data['items'][i]['item_basic']['images'])
                    item_price = data['items'][i]['item_basic']['price'] / 100000
                    item_url = f'{BASE_URL}{item_name.replace(" ", "-") + f"-i.{shop_id}.{item_id}"}'

                    product_shop_ids.append(shop_id)
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
    header = ['shop_id', 'item_id', 'item_name', 'item_image', 'item_price', 'item_url']
    with open('shopee_mall_product_info.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(header)

        writer.writerows(
            zip(product_shop_ids, item_ids, item_names, item_images, item_prices, item_urls))

def get_shopee_mall_product_from_shop_id_v2():
    '''
        This process to scrape data same with get_shopee_mall_product_from_shop_id(), 
        but I reorganize the scrape data to the right format
    '''
    shop_ids = []
    shop_item_counts = []  # use this for grequests, otherwise remove it
    with open('shopee_mall_detail_info.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        for row in csv_reader:
            shop_ids.append(row[0])
            # use this for grequests, otherwise remove it
            shop_item_counts.append(int(row[6]))

    BASE_URL = 'https://shopee.com.my/'

    scrape_day = datetime.today().strftime('%Y-%m-%d')
    scrape_major = 'my_mall'
    __location__ = os.path.abspath('/Users/thanhninh/Documents/abc-studio/day1-webscraping')
    result_path = os.path.join(__location__, 'shopee_scrape_result', scrape_day)
    isExist = os.path.exists(result_path)
    if not isExist:
        os.makedirs(result_path)

    # Using grequests to fetch data from api
    # start = time.time()
    for shop_id in shop_ids:
        print(shop_ids.index(shop_id))
        all_shop_items = []
        all_products_apis = []
        idx = shop_ids.index(shop_id)
        offset = 0
        limit = 100
        while True:
            all_products_apis.append(
                f'https://shopee.my/api/v4/shop/search_items?limit={limit}&shopid={shop_id}&offset={offset}')
            if offset <= shop_item_counts[idx]:
                if offset + limit >= shop_item_counts[idx]:
                    break
                else:
                    offset += limit
        # print(len(all_products_apis))
        reqs = (grequests.get(url) for url in all_products_apis)
        resps = grequests.imap(reqs, size=50)

        for resp in resps:
            try:
                data = json.loads(resp.text)
                if data['total_count'] == 0:
                    print(f'no more even offset less than total')
                else:
                    shop_items = data['items']
                    # item_basic = shop_items['item_basic']
                    # item_id = shop_items['']
                    # for item in shop_items:
                    #     item_id = item['itemid']
                    #     item['product_link'] = f"{BASE_URL}/product/{shop_id}/{item_id}"
                    all_shop_items.extend(shop_items)
            except:
                print(f'request failed: {resp}')
        for item in all_shop_items:
            del item['item_basic']['label_ids']
            shop_id = item['shopid']
            item_id = item['itemid']
            item['product_link'] = f"{BASE_URL}product/{shop_id}/{item_id}"

    # end = time.time()
    # print(f"Time taken for requests scraper: {end - start} seconds")

    # write data into a file
        json_name = f"x. SHOP_ID_{shop_id}_{scrape_major}_{scrape_day}.json"
        json_path = os.path.join(result_path, json_name)
        with open(json_path, 'w', encoding='utf8') as f:
            json.dump(all_shop_items, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    get_shopee_mall_basic_info()
    get_shopee_mall_detail_from_shop_id()
    # get_shopee_mall_product_from_shop_id()
    get_shopee_mall_product_from_shop_id_v2()

