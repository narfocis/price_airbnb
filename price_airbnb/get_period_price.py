"""
This is broken for now (2023-06-10). Airbnb has changed their API and the error is:
requests.exceptions.HTTPError: 400 Client Error: Bad Request for url: https://api.airbnb.com/v2/explore_tabs?toddlers=0&adults=0&infants=0&is_guided_search=true&version=1.4.8&section_offset=0&items_offset=0&screen_size=small&source=explore_tabs&items_per_grid=8&_format=for_explore_search_native&metadata_only=false&refinement_paths%5B%5D=%2Fhomes&timezone=Europe%2FLisbon&satori_version=1.1.0&query=Lisbon%2C+Portugal
"""
import datetime
import multiprocessing
import re
import numpy as np
import matplotlib.pyplot as plt

import airbnb

from price_airbnb.web_scrape import extract_listing, extract_prices


def get_period_price_from_api(start_date, end_date):
    api = airbnb.Api()
    # Offset the start date by the period
    print(start_date.strftime('%Y-%m-%d'))
    api.get_homes("Strasbourg, France", checkin=start_date.strftime('%Y-%m-%d'),
                  checkout=end_date.strftime('%Y-%m-%d'))


def build_urls(url, listings_per_page=20, pages_per_location=15):
    """Builds links for all search pages for a given location"""

    url_list = []
    for i in range(pages_per_location):
        offset = listings_per_page * i
        url_pagination = url + f'&items_offset={offset}'
        url_list.append(url_pagination)

    return url_list


def get_period_price_from_web(start_date, end_date):
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = end_date.strftime('%Y-%m-%d')
    url = "https://www.airbnb.fr/s/Strasbourg/homes?tab_id=home_tab&" \
          "refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&" \
          "monthly_start_date=2023-07-01&monthly_length=3&price_filter_input_type=0&" \
          "price_filter_num_nights=4&channel=EXPLORE&" \
          "query=Strasbourg%2C%20France&" \
          "place_id=ChIJwbIYXknIlkcRHyTnGDFIGpc&date_picker_type=calendar&" \
          f"checkin={start_date}&checkout={end_date}&" \
          "&adults=2&" \
          "source=structured_search_input_header&search_type=filter_change&min_bedrooms=1&min_beds=1&" \
          "min_bathrooms=1&l2_property_type_ids%5B%5D=3&room_types%5B%5D=Entire%20home%2Fapt"
    urls = build_urls(url)
    prices = extract_prices(url)
    return prices

def get_price_from_median(median_price, stay_length=4):
    """The median price is the price paid by the guest. It includes fees and such."""
    service_fee_guest = 0.15
    stay_tax = 3.3
    cleaning_fee = 20
    price = median_price / (1 + service_fee_guest) - stay_tax - cleaning_fee / stay_length
    return price

def get_final_price_between_dates(start_date, end_date, stay_length, queue):
    prices_dict = queue.get()
    period_prices = get_period_price_from_web(start_date, end_date)
    median_price = np.median(period_prices)
    price = get_price_from_median(median_price, stay_length=stay_length)
    price = np.round(price * 1.1)
    prices_dict[start_date] = price
    queue.put(prices_dict)

def main():
    start_date = datetime.date.today()
    period = 64
    stay_length = 4
    npoints = period // stay_length
    start_dates = [start_date + datetime.timedelta(days=i*stay_length) for i in range(npoints)]
    end_dates = [start_date + datetime.timedelta(days=(i+1)*stay_length) for i in range(npoints)]
    prices_dict = {}.fromkeys(start_dates)
    queue = multiprocessing.Queue()
    queue.put(prices_dict)
    processes = []
    for start, end in zip(start_dates, end_dates):
        # create a process
        processes.append(
            multiprocessing.Process(target=get_final_price_between_dates, args=(start, end, stay_length, queue))
        )
    # start the processes depending on the number of cores your machine has
    num_cores = multiprocessing.cpu_count() - 1
    for i in range(0, len(processes), num_cores):
        for j in range(num_cores):
            if i + j < len(processes):
                processes[i + j].start()
        for j in range(num_cores):
            if i + j < len(processes):
                processes[i + j].join()
    prices_dict = queue.get()
    print_str = '\n'.join([f'{k}: {v}' for k, v in prices_dict.items()])
    print(print_str)
    pass



if __name__ == '__main__':
    main()