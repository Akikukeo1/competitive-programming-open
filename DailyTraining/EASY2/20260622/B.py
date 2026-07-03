import sys


a, c = map(int, input().split())


def formater(num) -> int:
    return format(num, "b")


def main():
    base2A = formater(a)
    base2C = formater(c)

    sys.stderr.write(f"{base2A} {base2C}\n")

    print(format(a ^ c, "b"))


if __name__ == "__main__":
    main()
