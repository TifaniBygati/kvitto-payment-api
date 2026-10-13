def calculate_price(promo_code, price):
    discount = 0

    if promo_code == 'KVITTO10':
        discount = price * 10 // 100

    amount = price - discount

    return discount, amount

def calculate_schedule(amount, months):
    schedule = []

    base_payment = amount // months
    remainder = amount % months

    for i in range(months):
        if i < remainder:
            schedule.append(base_payment + 1)
        else:
            schedule.append(base_payment)


    return schedule