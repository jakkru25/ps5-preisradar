import json
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from monitor import extract_offer, is_digital_slim, identify_variant, check_all, price_number


def sample(product='Sony PlayStation 5 Slim Digital Edition', price='499.00', availability='InStock', extra=''):
    obj = {'@context': 'https://schema.org', '@type': 'Product', 'name': product,
           'offers': {'@type': 'Offer', 'priceCurrency': 'EUR', 'price': price,
                      'availability': 'https://schema.org/' + availability}}
    return '<html><script type="application/ld+json">' + json.dumps(obj) + '</script>' + extra + '</html>'


class MonitorTests(unittest.TestCase):
    def test_match(self):
        self.assertTrue(is_digital_slim('PlayStation 5 Slim Digital Edition'))
        self.assertTrue(is_digital_slim('SONY PS5 Digital Edition E-Chassis'))
        self.assertTrue(is_digital_slim('PS5 Slim Digital Edition'))
        self.assertFalse(is_digital_slim('PS5 Pro'))
        self.assertFalse(is_digital_slim('PS5 Controller Slim'))
        self.assertFalse(is_digital_slim('PlayStation 5 gebraucht Slim'))
        self.assertFalse(is_digital_slim('PlayStation 5 ohne Modellangabe'))
        self.assertTrue(is_digital_slim('PlayStation 5 Digital Edition 825GB CFI-2100 Slim'))
        self.assertFalse(is_digital_slim('PS5 Slim Disc Edition'))
        self.assertFalse(is_digital_slim('PS5 Slim mit Laufwerk'))
        self.assertFalse(is_digital_slim('PS5 Digital Edition 500 GB'))

    def test_offer(self):
        self.assertEqual(extract_offer(sample())[:2], (499, 'lieferbar'))
        self.assertEqual(extract_offer(sample(availability='OutOfStock'))[:2], (499, 'ausverkauft'))
        self.assertEqual(extract_offer(sample(product='PS5 Slim Disc Edition'), expected_variant='Digital')[1], 'nicht_auslesbar')
        self.assertEqual(extract_offer(sample(product='PS5 Slim Disc Edition'), expected_variant='Disc')[:2], (499, 'lieferbar'))
        self.assertEqual(identify_variant('PS5 Slim mit Laufwerk'), 'Disc')
        self.assertIsNone(identify_variant('PS5 Pro Disc Slim'))
        self.assertEqual(extract_offer(sample() + sample(price='599'))[1], 'mehrdeutig')

    def test_price_limit_750(self):
        notifications = []
        conf = {'max_price_eur': 750, 'watches': [{'id':'shop','shop':'Shop','url':'https://example.com'}]}
        first = check_all(conf, {}, 'topic', fetch=lambda _: (750,'lieferbar',None), push=lambda *args: notifications.append(args))
        self.assertEqual(len(notifications),1)
        self.assertEqual(first['max_price_eur'],750)
        check_all(conf, {}, 'topic', fetch=lambda _: (750.01,'lieferbar',None), push=lambda *args: notifications.append(args))
        self.assertEqual(len(notifications),1)

    def test_money(self):
        self.assertEqual(price_number('499,99 €'), 499.99)
        self.assertEqual(price_number('1.299,00 €'), 1299)
        self.assertIsNone(price_number('n/a'))

    def test_push_once_until_price_drops(self):
        alerts = []
        config = {'max_price_eur': 750, 'watches': [{'id': 'sony', 'shop': 'Sony', 'url': 'https://direct.playstation.com/test'}]}
        def push(*args):
            alerts.append(args)
        first = check_all(config, {}, 'topic-secret', fetch=lambda _: (520, 'lieferbar', None), push=push)
        self.assertEqual(len(alerts), 1)
        second = check_all(config, first, 'topic-secret', fetch=lambda _: (520, 'lieferbar', None), push=push)
        self.assertEqual(len(alerts), 1)
        third = check_all(config, second, 'topic-secret', fetch=lambda _: (499, 'lieferbar', None), push=push)
        self.assertEqual(len(alerts), 2)
        self.assertNotIn('topic-secret', json.dumps(third))

    def test_no_alert_for_unknown_stock(self):
        alerts = []
        config = {'max_price_eur': 750, 'watches': [{'id': 'x', 'shop': 'shop', 'url': 'https://example.com'}]}
        result = check_all(config, {}, 'topic-secret', fetch=lambda _: (400, 'unbekannt', None), push=lambda *a: alerts.append(a))
        self.assertFalse(alerts)
        self.assertEqual(result['offers'][0]['status'], 'unbekannt')

if __name__ == '__main__':
    unittest.main()
