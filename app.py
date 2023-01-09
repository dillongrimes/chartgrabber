import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from flask import redirect, Flask, request, render_template, url_for
from requests_html import HTMLSession

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        page_ref = request.values.get('page_ref')
        return redirect(url_for('output', page_ref=page_ref), code=302)

    return render_template(
        'home.html'
    )


@app.route('/<page_ref>')
def output(page_ref):
    error, url_bit, page_url = None, None, None
    output = ''
    # Is the reference a subgroup or item level page?
    subgroup = re.match(r'(bl_\d+)', page_ref, re.IGNORECASE)
    item_level = re.match(r'([hs]-\w+)', page_ref, re.IGNORECASE)
    if subgroup:
        url_bit = f"{subgroup[0]}/x"
    elif item_level:
        url_bit = f"Product/Detail/{item_level[0]}/X/X"
    else:
        error = f'unrecognized reference: {page_ref}. Please put in H-1234 or BL_1234'

    # contruct a url from the page_ref
    if url_bit:
        page_url = f"https://www.uline.com/{url_bit}"
        # fetch the page from the production website
        page = requests.get(page_url)
        # s = HTMLSession()
        # page = s.get(page_url)
        # page.html.render(wait=2, sleep=3)
        if not page.status_code == 200:
            error = f"Bad response: {page.status_code}"
        else:
            raw_html = page.text

            soup = BeautifulSoup(raw_html, 'html.parser')
            chartheader = soup.find("div", {"id": "dvRootItem"})
            if chartheader:
                output += str(chartheader)

            # find the dvChart
            chart = soup.find("div", {"id": "dvChart"})
            # drop the attrib tags
            [x.unwrap() for x in chart.findAll('attrib')]
            # remove any script tags
            [x.decompose() for x in chart.findAll('script')]
            # find the text "IN STOCK" and add a class to its container
            instock = chart.find(text=re.compile("IN STOCK"))
            if instock:
                instock.parent.get('class').append('inStockMessage')
            # make all urls absolute
            for url in chart.find_all('a'):
                url['href'] = urljoin('https://www.uline.com/', url.get('href'))
            for url in chart.find_all('link'):
                url['href'] = urljoin('https://www.uline.com/', url.get('href'))

            if chart:
                output += str(chart)

    return render_template(
        'output.html',
        error=error,
        output=output,
        page_ref=page_ref,
        page_url=page_url
    )


if __name__ == '__main__':
    app.run()
