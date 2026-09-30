import string

ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(ALPHABET)


def encode_base62(num: int) -> str:
    if num == 0:
        return ALPHABET[0]

    arr = []
    while num:
        num, rem = divmod(num, BASE)
        arr.append(ALPHABET[rem])

    arr.reverse()
    return "".join(arr)


def decode_base62(string_id: str) -> int:
    num = 0
    try:
        for char in string_id:
            num = num * BASE + ALPHABET.index(char)
        return num
    except ValueError:
        raise ValueError("Невалидный символ в Base62 строке")
