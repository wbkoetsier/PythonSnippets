from zeep import Client, helpers as zeephelpers, exceptions as ze

"""Use Zeep (https://github.com/mvantellingen/python-zeep) to make a SOAP request"""


class SomeError(Exception):
    """Some relevant custom exception"""
    pass

if __name__ == '__main__':
    # client = Client(wsdl='http://ec.europa.eu/taxation_customs/vies/checkVatTestService.wsdl')
    client = Client(wsdl='http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl')

    try:
        # Zeep removes the time zone from the xsd:Date
        # TODO https://github.com/mvantellingen/python-zeep/issues/769
        response = client.service.checkVat(countryCode='BE', vatNumber='0878065378')
    except ze.Fault as zf:
        raise SomeError(f'Zeep or VIES reported a problem: {zf}')
    print(zeephelpers.serialize_object(response))
    # OrderedDict([('countryCode', 'BE'), ('vatNumber', '0878065378'), ('requestDate', datetime.date(2018, 9, 19)),
    # ('valid', True), ('name', 'NV GOOGLE BELGIUM'), ('address', 'STEENWEG OP ETTERBEEK 180\n1040 BRUSSEL')])

