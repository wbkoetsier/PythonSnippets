# https://www.codewars.com/kata/53368a47e38700bd8300030d

def namelist(names):
    names_list = [n['name'] for n in names]
    if len(names_list) > 1:
        return ', '.join(names_list[:-1]) + ' & ' + names_list[-1]
    elif len(names_list) == 1:
        return names_list[-1]
    else:
        return ''


if __name__ == '__main__':
    print(namelist([{'name': 'Bart'}, {'name': 'Lisa'}, {'name': 'Maggie'}]))
