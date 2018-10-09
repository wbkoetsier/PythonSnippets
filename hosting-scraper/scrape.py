import requests
from bs4 import BeautifulSoup
from collections import namedtuple
import re
from typing import List, Union
import csv
from decimal import Decimal


def get_soup_from_url(url, params: dict={}):
    """Return soup of html of this page (params are fixed)"""
    print('fetch', url)
    r = requests.get(url, params=params)
    if not r.status_code == 200:
        return 0
    print('response:', r)
    return BeautifulSoup(r.content, 'html.parser')


def calculate_nsp(pos_reviews: Union[int, str]) -> int:
    """Return NPS, calculated off of the number of positive reviews per 100, or 0 if it can't be calculated"""
    try:
        # so if there are 0 or very little % positive reviews, this nsp goes below 0
        return 100 - ((100 - int(pos_reviews)) * 2)
    except (ValueError, TypeError):
        # maybe pos_reviews was empty or couldn't be converted to an int
        return 0


def calculate_estimated_revenue(fte: Union[int, float, str]):
    """Return the estimated revenue in M euro calculated off of the number of fte, or 0 if it can't be calculated"""
    try:
        return Decimal(float(fte) * .2).quantize(Decimal('1.0'))
    except (ValueError, TypeError) as e:
        # maybe fte was empty or couldn't be converted to an int
        return 0


def read_card_details(soup, clas: str, subjects: List[tuple]) -> dict:
    """Return dictionary with the desired company info card details.

    The card consists of uls, find the correct li based on the header and extract the details

    @:param soup: soup of entire isp page
    @:param clas: the class of the header div
    @:param subjects: list of tuples of detail name and dict key
    """
    result = {}
    # find the header div
    header = soup.find('div', {'class': clas})
    # find the ul this header is found in
    ul = header.parent.parent
    # iterate over the li items to find the ones with the desired detail name, when found, store value under key
    li = ul.find_all('li')
    for item in li:
        if not item.p:
            continue
        subj_name = item.p.text.strip()
        for subj in subjects:
            if subj_name == subj[0]:
                # sometimes span is used, sometimes no tag, just text
                if item.span:
                    res = item.span.text.strip()
                else:
                    # hack for missing </li> tags!
                    res = [i for i in item.p.next_siblings][0].strip()
                # if the result is a number, store it as a number
                try:
                    res = float(res) if '.' in res else int(res)
                except (ValueError, TypeError):
                    pass
                result[subj[1]] = res

    return result


def scrape_isps(filename: str='./isps.csv'):
    """Scrape ISP data and write to csv"""
    # list of rows for each ISP the query finds
    result_rows = []

    # query: in the Netherlands and a minimum of 5 employees
    params = dict(
        action='zoek',
        naam='',
        plaats='',
        land='Nederland',
        beoordeling_min='', beoordeling_max='',
        ervaringen_min='', ervaringen_max='',
        medewerkers_min='5', medewerkers_max='')

    page_num = 0
    # for each subsequent page of 25 isps, get the page and collect details
    while True:
        # get overview page soup
        url = "https://www.ispgids.com/overzicht/" + str(page_num * 25)
        soup = get_soup_from_url(url, params)
        # and increase page num
        page_num += 1

        # each isp is on a new row, paging might be needed
        isps = []
        isps_table = soup.find('table', attrs={'class': 'table'})
        table_body = isps_table.find('tbody')
        rows = table_body.find_all('tr')
        # stop this when no more results are found
        if 'Geen ISP\'s gevonden op basis van uw criteria.' in table_body.text:
            break

        # gather name, link and nsp for each of the isps shown on the page
        for row in rows:
            # find the link to the ISP-page in the second column
            cols = row.find_all('td')
            link = cols[1]
            # calculate NPS (100 - ('number of negative reviews per 100' * 2))
            review = cols[6]
            sm = re.search('([0-9]*) uit 100', review.text)
            pos = sm.group(1) if sm else ''
            isps.append(dict(
                name=link.a.string.strip(),
                href='https://www.ispgids.com' + link.a['href'],
                nsp=calculate_nsp(pos)))

        # visit each isp page and gather the details from the cards
        for isp in isps:
            isp_soup = get_soup_from_url(isp.get('href'))
            if not isp_soup:
                continue
            # start with the details that were already on the overview page
            result = {'name': isp.get('name'),
                      'netPromotorScore': isp.get('nsp')}
            # get details from the description card
            card_text = isp_soup.find('div', attrs={'class': 'officieeleinfo'}).parent.text
            services_match = re.search('.*biedt de volgende diensten aan:\n(.*)\n', card_text)
            services = services_match.group(1) if services_match else ''
            result['servicesOffered'] = services
            result['resellersSupported'] = 1 if re.search('[ -]resel', services) else ''
            # get address details
            result.update(read_card_details(isp_soup, 'adres', [
                ('Adres', 'streetAddress'),
                ('Postcode', 'postalCode'),
                ('Plaats', 'addressLocality')]))
            # get numbers
            result.update(read_card_details(isp_soup, 'aantal', [
                ('Aantal klanten', 'numberOfCustomers'),
                ('Aantal domeinen', 'numberOfDomains'),
                ('Aantal servers', 'numberOfServers')]))
            # get company info
            result.update(read_card_details(isp_soup, 'bedrijfsinfo', [
                ('Opgericht', 'yearFounded'),
                ('Personeel Totaal', 'numberOfFte')]))
            # calculate estimated revenue from number of fte
            result['estimatedRevenue'] = calculate_estimated_revenue(result['numberOfFte'])
            # append the results to the main list of rows
            result_rows.append(result)

    print('found {} isps'.format(len(result_rows)))
    for rr in result_rows:
        print(rr)

    # TODO: write the results to CSV
    Columns = namedtuple("Columns", ['name', 'displayName'])
    # we want to fill the following fields, in this order:
    column_names = (Columns('name', 'Naam',),
                    Columns('streetAddress', 'Adres'),
                    Columns('postalCode', 'Postcode'),
                    Columns('addressLocality', 'Plaats'),
                    Columns('yearFounded', 'Opgericht'),
                    Columns('numberOfCustomers', 'Klanten'),
                    Columns('numberOfDomains', 'Domeinen'),
                    Columns('numberOfServers', 'Servers'),
                    Columns('numberOfFte', 'Medewerkers (fte)'),
                    Columns('netPromotorScore', 'NPS (%)'),
                    Columns('resellersSupported', 'Resellers toegestaan'),
                    Columns('estimatedRevenue', 'Geschatte omzet (*miljoen euro)'),
                    Columns('servicesOffered', 'Diensten'))

    print('write csv')
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [i[0] for i in column_names]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # write custom header
        writer.writerow({c.name: c.displayName for c in column_names})
        # write data
        for rd in result_rows:
            try:
                writer.writerow(rd)
            except Exception as e:
                print(e)
                print(rd)

        # writer.writerows(result_rows)

    print('done')

if __name__ == '__main__':
    scrape_isps()