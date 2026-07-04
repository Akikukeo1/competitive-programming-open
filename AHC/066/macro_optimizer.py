import sys


def solve():
    # Read commands from stdin
    content = sys.stdin.read().strip()
    if not content:
        return

    base_actions = list(content)

    n = len(base_actions)

    # Try all substrings of length 2 to 10 as potential macro
    best_total = n
    best_macro = None

    # To speed up, only consider substrings that appear at least twice
    counts = {}
    for length in range(2, 11):
        for i in range(n - length + 1):
            sub = tuple(base_actions[i : i + length])
            counts[sub] = counts.get(sub, 0) + 1

    candidates = [sub for sub, count in counts.items() if count > 1]

    for sub in candidates:
        m_len = len(sub)
        dp = [0] * (n + 1)
        for i in range(1, n + 1):
            dp[i] = dp[i - 1] + 1
            if i >= m_len and tuple(base_actions[i - m_len : i]) == sub:
                dp[i] = min(dp[i], dp[i - m_len] + 1)

        total = dp[n] + m_len + 2
        if total < best_total:
            best_total = total
            best_macro = sub

    print(f"Best Macro: {best_macro}")
    print(f"Original Length: {n}")
    print(f"Compressed Length: {best_total}")


# If we want to use multiple macros (overwriting), it's a bit more complex.
# dp[i] = min(dp[i-1]+1, min_{m} (dp[j] + |m| + 2 + usage_of_m_in_S[j:i]))
# This is O(N^3) or O(N^2) with some tricks.

if __name__ == "__main__":
    solve()
