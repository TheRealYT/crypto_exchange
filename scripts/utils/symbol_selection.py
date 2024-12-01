import numpy as np


def select_uncorrelated_symbols(correlation_matrix, num_symbols=30):
    min_avg_correlation = float('inf')
    min_correlation_symbols = []

    for symbol, related_symbols in correlation_matrix.items():
        cnt = 0
        avg_correlation = 0
        symbols = [symbol]
        sym = symbol

        while cnt < num_symbols - 1:
            related_symbols = correlation_matrix[sym].items()

            min_correlation = float('inf')
            min_symbol = None

            for name, correlation in related_symbols:
                if name in symbols or np.isnan(correlation):
                    continue

                if correlation < min_correlation:
                    min_correlation = correlation
                    min_symbol = name

            if min_symbol is not None:
                symbols.append(min_symbol)
                cnt += 1
                sym = min_symbol
                avg_correlation += min_correlation
                continue
            else:
                break

        avg_correlation /= num_symbols
        if avg_correlation < min_avg_correlation and len(symbols) >= len(min_correlation_symbols):
            min_avg_correlation = avg_correlation
            min_correlation_symbols = symbols

    return min_correlation_symbols
