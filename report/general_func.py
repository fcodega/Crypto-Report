def complete_year_list(y_list):

    min_y = min(y_list)
    max_y = max(y_list)

    complete_y = []

    for i in range(min_y, max_y + 1):
        complete_y.append(i)

    return complete_y


def extend_pivot_header(pivot_df, y_list, filled_value):

    incomplete_y = pivot_df.columns
    complete_y = complete_year_list(y_list)

    for el in incomplete_y:
        complete_y.remove(el)

    missing_y = complete_y

    for y in missing_y:
        pivot_df[y] = filled_value

    pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)

    return pivot_df
