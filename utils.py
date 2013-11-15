

def jsonify(obj):
    d = {}
    for field in obj:
        field_data = obj[field]
        datatype = str(type(field_data))
        if 'unicode' in datatype or 'int' in datatype:
            d[str(field)] = field_data
        elif 'ObjectId' in datatype:
            d['id'] = str(field_data)
        elif 'schema' in datatype:
            d[str(field)] = jsonify(field_data)
        elif 'None' in datatype:
            d[str(field)] = ''
        else:
            pass
    return d


if __name__ == '__main__':
    from schema import *
    connect('carpools')
    driver = Driver.objects.first()
    from pprint import pprint
    pprint(  jsonify(driver) )
