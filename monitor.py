"""PS5 Slim Digital/Disc cloud monitor. Public measurements, private push topic."""
import ipaddress
import json
import os
import re
import socket
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'docs' / 'data.json'
AGENT = {'User-Agent': 'Mozilla/5.0 (compatible; PS5Preisradar/3.0; product monitoring)'}
ALLOWED_HOSTS = {
    'direct.playstation.com', 'www.mediamarkt.de', 'www.saturn.de',
    'www.amazon.de', 'www.otto.de', 'www.galaxus.de', 'www.expert.de',
    'www.smythstoys.com', 'www.coolblue.de', 'www.alternate.de', 'www.cyberport.de',
}


def validate_url(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Nur Produktseiten erlaubter HTTPS-Shops sind zulässig.')
    # Defense in depth against DNS-based internal network access.
    for answer in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(answer[4][0]).is_global:
            raise ValueError('Shop-Host löst auf eine nicht öffentliche Adresse auf.')
    return url


def price_number(value):
    if value is None or isinstance(value, bool):
        return None
    s = re.sub(r'[^\d.,-]', '', str(value))
    if not s:
        return None
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    elif s.count('.') > 1:
        s = s.replace('.', '')
    try:
        value = Decimal(s)
    except InvalidOperation:
        return None
    return float(value) if value.is_finite() and 50 <= value <= 10000 else None


def identify_variant(name):
    """Return 'Digital' or 'Disc' only for clear new PS5 Slim console names."""
    if not isinstance(name, str):
        return None
    normalized = name.lower().replace('ü','ue').replace('ö','oe').replace('ä','ae').replace('ß','ss')
    normalized = re.sub(r'[^a-z0-9]+', ' ', normalized)
    tokens = set(normalized.split())
    if not ('ps5' in tokens or 'playstation 5' in normalized or 'playstation5' in tokens):
        return None
    if any(re.search(r'\b'+token+r'\b', normalized) for token in (
        'pro','controller','dualsense','portal','refurbished','generaluberholt',
        'generalueberholt','gebraucht','renewed','zubehor','zubehoer',
        'bundle','paket','spiel','ladestation','standfuss','disc drive',
        'laufwerk separat','ersatzlaufwerk','ps5 fat',
    )):
        return None
    slim = ('slim' in tokens or 'cfi 20' in normalized or 'cfi 21' in normalized or
            'd chassis' in normalized or 'e chassis' in normalized or 'modellgruppe slim' in normalized)
    if not slim:
        return None
    digital = 'digital' in tokens or 'ohne laufwerk' in normalized
    disc = ('disc' in tokens or 'disk' in tokens or 'mit laufwerk' in normalized or
            'standard edition' in normalized)
    if digital and disc:
        return None
    return 'Digital' if digital else ('Disc' if disc else None)


def is_digital_slim(name):
    """Kept for backwards compatibility with older integrations."""
    return identify_variant(name) == 'Digital'


def flatten_jsonld(value):
    if isinstance(value, list):
        for item in value:
            yield from flatten_jsonld(item)
    elif isinstance(value, dict):
        yield value
        for key in ('@graph',):
            if key in value:
                yield from flatten_jsonld(value[key])


def extract_offer(html, expected_variant=None):
    soup = BeautifulSoup(html, 'html.parser')
    offers = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        for product in flatten_jsonld(data):
            types = product.get('@type', [])
            if isinstance(types, str):
                types = [types]
            if not any(str(t).lower().endswith('product') for t in types):
                continue
            variant = identify_variant(product.get('name'))
            if variant is None or (expected_variant and variant != expected_variant):
                continue
            raw_offers = product.get('offers', [])
            if isinstance(raw_offers, dict):
                raw_offers = [raw_offers]
            if not isinstance(raw_offers, list):
                continue
            for offer in raw_offers:
                if not isinstance(offer, dict) or offer.get('priceCurrency') != 'EUR':
                    continue
                value = offer.get('price')
                if value is None and isinstance(offer.get('priceSpecification'), dict):
                    value = offer['priceSpecification'].get('price')
                price = price_number(value)
                if price is None:
                    continue
                availability = offer.get('availability', '')
                if isinstance(availability, dict):
                    availability = availability.get('@id', '')
                status = str(availability).rsplit('/', 1)[-1].lower()
                stock = 'lieferbar' if status in ('instock', 'limitedavailability', 'onlineonly') else ('ausverkauft' if status in ('outofstock', 'soldout', 'discontinued') else 'unbekannt')
                offers.append((price, stock))
    if not offers:
        return None, 'nicht_auslesbar', 'Keine eindeutigen strukturierten PS5-Slim-Produktdaten für die Variante'
    if len(set(offers)) != 1:
        return None, 'mehrdeutig', 'Mehrere abweichende Angebote, möglicherweise Marktplatz'
    price, status = offers[0]
    return price, status, None


def fetch_offer(url, variant=None):
    validate_url(url)
    response = requests.get(url, headers=AGENT, timeout=(8, 18), allow_redirects=False)
    if response.status_code in (403, 429):
        raise ValueError(f'Shop blockiert Abfrage (HTTP {response.status_code})')
    if 300 <= response.status_code < 400:
        raise ValueError('Weiterleitung: finale Produkt-URL nötig')
    response.raise_for_status()
    if 'html' not in response.headers.get('content-type', '').lower():
        raise ValueError('Antwort ist kein HTML')
    if len(response.content) > 4_000_000:
        raise ValueError('Shop-Antwort zu groß')
    return extract_offer(response.text, expected_variant=variant)


def send_push(topic, watch, price, limit):
    msg = f"PS5 Slim {watch.get('variant', 'Digital/Disc')} bei {watch['shop']}: {price:.2f} EUR (Limit: {limit:.2f} EUR). Versand, Händler und Lieferzeit vor Kauf prüfen!\n{watch['url']}"
    response = requests.post('https://ntfy.sh/' + quote(topic, safe=''),
                             data=msg.encode('utf-8'), timeout=15,
                             headers={'Title': 'PS5 Preisalarm', 'Priority': 'high',
                                      'Tags': 'video_game', 'Click': watch['url']})
    response.raise_for_status()


def check_all(config, previous, topic, fetch=fetch_offer, push=send_push):
    watches = config['watches']
    max_price = float(config['max_price_eur'])
    if not 50 <= max_price <= 10000:
        raise ValueError('max_price_eur außerhalb des gültigen Bereichs')
    if len(watches) > 30:
        raise ValueError('Maximal 30 Produkte')
    if len({w['id'] for w in watches}) != len(watches):
        raise ValueError('Doppelte Watch-IDs')
    # Don't reuse stale single-variant alert state.
    if previous.get('model') != 'PS5 Slim (Digital oder Disc)':
        previous = {}
    old = {x['id']: x for x in previous.get('offers', [])}
    checked = datetime.now(timezone.utc).isoformat(timespec='seconds')
    result = []
    for watch in watches:
        url = watch['url']
        item = {'id': watch['id'], 'shop': watch['shop'], 'variant': watch.get('variant', 'Digital'), 'url': url,
                'price': None, 'status': 'fehler', 'error': None, 'checked_at': checked}
        try:
            try:
                item['price'], item['status'], item['error'] = fetch(url, watch.get('variant'))
            except TypeError:
                # Allow older one-argument fetch fakes used by third-party clients.
                item['price'], item['status'], item['error'] = fetch(url)
        except (requests.RequestException, OSError, ValueError) as exc:
            item['error'] = str(exc)[:180]
        prior = old.get(watch['id'], {})
        # Keep alert state independent from latest transient scrape errors.
        last_alert_price = prior.get('last_alert_price')
        was_eligible = prior.get('status') == 'lieferbar' and prior.get('price') is not None and prior['price'] <= max_price
        eligible = item['status'] == 'lieferbar' and item['price'] is not None and item['price'] <= max_price
        improved = last_alert_price is not None and item['price'] is not None and item['price'] < last_alert_price - .009
        notify = eligible and (not was_eligible or last_alert_price is None or improved)
        item['last_alert_price'] = last_alert_price
        item['last_alert_at'] = prior.get('last_alert_at')
        if notify and topic:
            try:
                push(topic, watch, item['price'], max_price)
                item['last_alert_price'] = item['price']
                item['last_alert_at'] = checked
                print(f"Alarm gesendet: {watch['shop']}")
            except requests.RequestException as exc:
                print(f"Push fehlgeschlagen ({watch['shop']}): {exc}")
        elif notify and not topic:
            print('Kein NTFY_TOPIC Secret hinterlegt; Push deaktiviert')
        result.append(item)
    history = previous.get('history', [])
    history.append({'checked_at': checked, 'offers': [{'id': o['id'], 'price': o['price'], 'status': o['status']} for o in result]})
    return {'model': 'PS5 Slim (Digital oder Disc)', 'max_price_eur': max_price,
            'good_deal_eur': float(config.get('good_deal_eur', 600)),
            'checked_at': checked, 'offers': result, 'history': history[-120:]}


def main():
    config = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
    previous = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    output = check_all(config, previous, os.getenv('NTFY_TOPIC', '').strip())
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Überprüft:', len(output['offers']), '| Treffer:', sum(o['status'] == 'lieferbar' and o['price'] is not None and o['price'] <= output['max_price_eur'] for o in output['offers']))


if __name__ == '__main__':
    main()
