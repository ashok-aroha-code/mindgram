def linear_search(arr, x):
    for i in range(len(arr)):
        if arr[i] == x:
            return i
    return -1
arr = [1, 12, 3, 45, 5, 67]
x = 67
print(linear_search(arr, x))    