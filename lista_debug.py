
# partition vai divir o array em duas metade
def partition(arr, left, right):
    
    pivot = arr[right] # pivô é o último elemento
    i = left -1 # índice do menor elemento
    
    # Na primeira iteração vai ser o array inteiro ex [1,2,3,4,5]
    for j in range(left, right):
        if arr[j] <= pivot:
            i = i +1
            arr[i], arr[j] = arr[j], arr[i]
        
    arr[i+1], arr[right] = arr[right], arr[i+1]  # coloca pivô na posição correta
    return i+1

def quicksort(arr, left, right):
    
    if left < right:
        pivot = partition(arr, left, right)
        quicksort(arr, left, pivot - 1)
        quicksort(arr, pivot + 1, right)
    
    return arr
        
        

    
arr = [10, 7, 8, 9, 1, 5]
quicksort(arr, 0, len(arr) - 1) # len(arr) -1 : Pegando o ultomo indice da lista [5]
print('Array final:', arr)




# Exercício 1 – Ordenando números

def patition(array, left, right):
    
    pivot = array[right] # pivot é o ultimo elemento
    i = left -1 # indice do primeiro elemento
    
    for j in range(left, right):
        if array[j] <= pivot: # se o primeiro indice for menor que o ultimo
            
            i = i + 1
            array[i], array[j] = array[j], array[i] # Trocando a posição dos elementos
    # Colocar o pivo na posição correta
    array[i + 1], array[right] = array[right], array[i + 1]
    return i+1
    

def quicksort_exe(array, left, right):
    
    if left < right:
        pivot = patition(array, left, right)
        quicksort_exe(array, left, right - 1)
        quicksort_exe(array, pivot + 1, right)
        
    
        
array = [10, 7, 8, 9, 1, 5]
quicksort(array, 0, len(array) - 1)
print(array)