import numpy as np

# 1. FBPICK → sample через DT.
# 2. Проверяем амплитуду в точке пикировки.
# 3. Положительная фаза → pick оставляем.
# 4. Отрицательная фаза → ищем положительную фазу слева и справа
#    через 2 перехода через 0.
# 5. На каждой найденной фазе определяем максимум амплитуды.
# 6. Если кандидата два — строим локальную гладкую траекторию FBPICK
#    только по валидным положительным picks.
# 7. Сравниваем кандидаты с траекторией.
# 8. LEFT выбираем по умолчанию, RIGHT только если он заметно лучше
#    (RIGHT_MARGIN_MS).


PREDICTION_WINDOW = 5
RIGHT_MARGIN_MS = 0.5


def find_positive_peak(trace, sample, direction):
    """Find positive-phase peak to the left or right of sample."""

    n_samples = len(trace)
    crossings = []

    if direction == -1:
        indices = range(sample, 0, -1)
    else:
        indices = range(sample, n_samples - 1)

    for index in indices:
        if direction == -1:
            left = trace[index - 1]
            right = trace[index]
        else:
            left = trace[index]
            right = trace[index + 1]

        if left * right <= 0:
            crossings.append(index)

            if len(crossings) == 2:
                break

    if len(crossings) < 2:
        return None

    if direction == -1:
        start = crossings[1]
        end = crossings[0]
    else:
        start = crossings[0]
        end = crossings[1]

    segment = trace[start : end + 1]
    positive = segment > 0

    if not np.any(positive):
        return None

    candidates = np.where(positive)[0]

    return start + candidates[np.argmax(segment[candidates])]


def exec(traces, headers, headers_dictionary):

    n_traces, n_samples = traces.shape
    n_headers = headers.shape[1]

    fbpick_index = headers_dictionary.get(
        "FBPICK",
        n_headers,
    )

    dt_index = headers_dictionary.get(
        "dt",
        n_headers,
    )

    if fbpick_index >= n_headers or dt_index >= n_headers:
        return traces, headers

    original_picks = headers[:, fbpick_index].copy()
    filtered_picks = original_picks.copy()

    # --------------------------------------------------
    # Find picks located on a positive phase
    # --------------------------------------------------

    valid_pick = np.zeros(
        n_traces,
        dtype=bool,
    )

    for i in range(n_traces):
        pick = original_picks[i]
        dt = headers[i, dt_index]

        if (
            not np.isfinite(pick)
            or not np.isfinite(dt)
            or pick <= 0
            or dt <= 0
        ):
            continue

        sample = int(round(pick / dt))

        if not 0 <= sample < n_samples:
            continue

        valid_pick[i] = traces[i, sample] > 0

    # --------------------------------------------------
    # Correct picks located on a negative phase
    # --------------------------------------------------

    for i in range(n_traces):
        if valid_pick[i]:
            continue

        pick = original_picks[i]
        dt = headers[i, dt_index]

        if (
            not np.isfinite(pick)
            or not np.isfinite(dt)
            or pick <= 0
            or dt <= 0
        ):
            continue

        sample = int(round(pick / dt))

        if not 0 <= sample < n_samples:
            continue

        left_index = find_positive_peak(
            traces[i],
            sample,
            direction=-1,
        )

        right_index = find_positive_peak(
            traces[i],
            sample,
            direction=1,
        )

        # No positive phase found
        if left_index is None and right_index is None:
            continue

        # Only right phase found
        if left_index is None:
            filtered_picks[i] = right_index * dt
            continue

        # Only left phase found
        if right_index is None:
            filtered_picks[i] = left_index * dt
            continue

        left_pick = left_index * dt
        right_pick = right_index * dt

        # --------------------------------------------------
        # Build local trajectory from valid picks only
        # --------------------------------------------------

        start = max(
            0,
            i - PREDICTION_WINDOW,
        )

        end = min(
            n_traces,
            i + PREDICTION_WINDOW + 1,
        )

        x_values = []
        y_values = []

        for j in range(start, end):
            if j == i or not valid_pick[j]:
                continue

            x_values.append(j)
            y_values.append(original_picks[j])

        # Not enough valid points:
        # LEFT is the default choice.
        if len(x_values) < 3:
            filtered_picks[i] = left_pick
            continue

        # --------------------------------------------------
        # Local quadratic prediction
        # --------------------------------------------------

        coefficients = np.polyfit(
            x_values,
            y_values,
            2,
        )

        expected_pick = np.polyval(
            coefficients,
            i,
        )

        left_error = abs(left_pick - expected_pick)

        right_error = abs(right_pick - expected_pick)

        # --------------------------------------------------
        # RIGHT must be significantly better than LEFT
        # --------------------------------------------------

        if right_error + RIGHT_MARGIN_MS < left_error:
            filtered_picks[i] = right_pick
        else:
            filtered_picks[i] = left_pick

    headers[:, fbpick_index] = filtered_picks

    return traces, headers
