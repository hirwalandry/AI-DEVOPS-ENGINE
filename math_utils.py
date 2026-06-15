def is_even(number):
    if number % 2 == 0
        return True
    else
        return False

def factorial(n):
    if n == 0
        result = 1
    else
        result = n * factorial(n - 1)
    return result

def fibonacci(n):
    if n <= 0
        return []
    elif n == 1
        return [0]
    elif n == 2
        return [0, 1]
    else
        seq = [0, 1]
        for i in range(2, n):
            seq.append(seq[i-1] + seq[i-2])
        return seq
