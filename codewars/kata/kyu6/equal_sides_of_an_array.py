# https://www.codewars.com/kata/5679aa472b8f57fb8c000047
def find_even_index(arr):
    return (sorted([i for i in range(len(arr)) if sum(arr[0:i]) == sum(arr[i + 1:])])[0:1] or [-1])[0]
