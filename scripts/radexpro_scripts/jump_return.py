import numpy as np

THRESHOLD_MS = 1.0


def exec(traces, headers, headers_dictionary):

    n_traces, n_headers = headers.shape

    fbpick_index = headers_dictionary.get(
        "FBPICK",
        n_headers,
    )

    if fbpick_index >= n_headers or n_traces < 3:
        return traces, headers

    picks = headers[:, fbpick_index].copy()

    for i in range(1, n_traces - 1):
        prev_pick = picks[i - 1]
        current_pick = picks[i]
        next_pick = picks[i + 1]

        if (
            not np.isfinite(prev_pick)
            or not np.isfinite(current_pick)
            or not np.isfinite(next_pick)
            or prev_pick <= 0
            or current_pick <= 0
            or next_pick <= 0
        ):
            continue

        jump_in = current_pick - prev_pick
        jump_out = next_pick - current_pick

        is_jump_return = (
            abs(jump_in) > THRESHOLD_MS
            and abs(jump_out) > THRESHOLD_MS
            and jump_in * jump_out < 0
        )

        if is_jump_return:
            picks[i] = (prev_pick + next_pick) / 2

    headers[:, fbpick_index] = picks

    return traces, headers
