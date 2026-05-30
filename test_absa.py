import re, json
import requests
from bs4 import BeautifulSoup

BASE_PAGE='https://my.absa.org/RiskGroups'
ENDPOINT='https://my.absa.org/tiki-search_customsearch-customsearch'

s=requests.Session()
s.headers.update({'User-Agent':'Mozilla/5.0','Accept-Language':'en-US,en;q=0.9'})
try:
    r=s.get(BASE_PAGE, timeout=30)
    print('GET status', r.status_code, 'len', len(r.text))
    html=r.text
    m=re.search(r"definition=([0-9a-f]{32})", html, flags=re.I)
    print('definition', m.group(1) if m else None)
    soup=BeautifulSoup(html,'html.parser')
    content_id=None
    for inp in soup.find_all('input'):
        cid = inp.get('id') or ''
        if cid.startswith('customsearch_rg_') and inp.get('type','').lower() in ('text','search',''):
            content_id=cid; break
    print('content_id', content_id)

    def post(term):
        if not content_id:
            print('No content_id found')
            return
        adddata=json.dumps({content_id:{'config':{'_filter':'content','type':'text'},'name':'input','value':term}}, separators=(',',':'))
        data={'definition':m.group(1) if m else 'deeb6df526292fb698072a3a6531a9ae','adddata':adddata,'searchid':'rg','offset':'0','maxRecords':'500','store_query':'','page':'Riskgroups','recalllastsearch':'1'}
        h={'Referer':BASE_PAGE,'X-Requested-With':'XMLHttpRequest'}
        rr=s.post(ENDPOINT, data=data, headers=h, timeout=30, allow_redirects=False)
        print(f"POST {term} status {rr.status_code} len {len(rr.text)} redirect {rr.headers.get('Location')}")
        text=rr.text
        print('contains <table', '<table' in text)
        print('contains customsearch_rg_results', 'customsearch_rg_results' in text)
        print('first200:', text[:200].replace('\n', ' '))
        print('last200:', text[-200:].replace('\n', ' '))

    post('bac*')
except Exception as e:
    import traceback
    print('Error:', e)
    traceback.print_exc()
