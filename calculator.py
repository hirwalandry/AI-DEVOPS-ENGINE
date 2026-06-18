def divide(a, b):
    return a / b  # crashes if b=0

def add(a, b):
    return a - b  # wrong operator

def get_user(user_id):
    users = {1: "Alice", 2: "lan"}
    return users[user_id]  # crashes if id not found

def format_greeting(name):
    return "Hello, " + nam  # NameError: 'nam' is not defined

def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        seq = [0, 1]
        for i in range(2, n):
            seq.append(seq[i-1] + seq[i-2])
        return seq