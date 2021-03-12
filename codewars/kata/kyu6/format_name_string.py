# https://www.codewars.com/kata/53368a47e38700bd8300030d

def namelist(names):
    if not names: return ''
    *first_names, last_name = iter(names)
    if first_names:
        return ', '.join([n['name'] for n in first_names]) + ' & ' + last_name['name']
    else:
        return last_name['name']
