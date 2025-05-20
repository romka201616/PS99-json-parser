import pandas as pd
from pathlib import Path
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- Расположения ---
INPUT_DIR = Path("input_csvs")
OUTPUT_DIR = Path("output_csvs")
CHARTS_DIR = Path("output_charts")

# --- Кол-во столбцов, расписанных по отдельности ---
N_TOP_COLUMNS_FOR_CHART = 10

# --- Шрифты ---
AXIS_LABEL_FONTSIZE = 14
AXIS_TICKS_FONTSIZE = 14
LEGEND_FONTSIZE = 16
TITLE_FONTSIZE = 12
BAR_LABEL_FONTSIZE = 14

# Расположение легенды:
# Строковые значения: 'best', 'upper right', 'upper left', 'lower left', 'lower right',
# 'right', 'center left', 'center right', 'lower center', 'upper center', 'center'
# Кортеж для bbox_to_anchor (вынос легенды за пределы графика): например, (1.02, 1)
# Если используется кортеж, loc для legend будет 'upper left' по умолчанию для bbox_to_anchor
LEGEND_LOCATION = 'upper left'  # ИЗМЕНЕНИЕ: Вы можете поменять это значение


# Например:
# LEGEND_LOCATION = 'best'
# LEGEND_LOCATION = (1.02, 1) # Легенда справа от графика
# LEGEND_LOCATION = 'center left'
# --------------------

def generate_stacked_bar_chart(df_for_chart: pd.DataFrame, chart_filepath: Path,
                               y_axis_label: str, original_time_col_name: str, # original_time_col_name теперь не используется для xlabel
                               indicator_col_name_for_legend: str):
    if df_for_chart.empty:
        print(f"  Данные для графика '{chart_filepath.name}' пусты. График не будет создан.")
        return

    df_plot = df_for_chart.copy()

    if isinstance(df_plot.index, pd.DatetimeIndex):
        df_plot.index = df_plot.index.strftime('%d-%m')

    if len(df_plot.columns) > N_TOP_COLUMNS_FOR_CHART:
        top_n_cols = list(df_plot.columns[:N_TOP_COLUMNS_FOR_CHART])
        other_cols = list(df_plot.columns[N_TOP_COLUMNS_FOR_CHART:])
        df_temp = df_plot[top_n_cols].copy()
        df_temp["Другое"] = df_plot[other_cols].sum(axis=1)
        df_plot = df_temp

    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except Exception as e:
        print(
            f"  Предупреждение: не удалось применить стиль 'seaborn-v0_8-whitegrid'. Используется стиль по умолчанию. Ошибка: {e}")
        pass

    ax = df_plot.plot(kind='bar', stacked=True, figsize=(18, 10), colormap='tab20')

    # Убираем или устанавливаем пустую метку для оси X
    ax.set_xlabel("", fontsize=AXIS_LABEL_FONTSIZE) # <--- ИЗМЕНЕНИЕ: Установлена пустая строка

    # Закомментированные строки для заголовка и метки Y, если они тоже не нужны:
    # ax.set_ylabel(y_axis_label, fontsize=AXIS_LABEL_FONTSIZE)
    # ax.set_title(f"Динамика \"{y_axis_label}\" по неделям (Топ {N_TOP_COLUMNS_FOR_CHART} и Другое)",
    #              fontsize=TITLE_FONTSIZE, pad=20)

    formatter = mticker.FuncFormatter(lambda x, p: format(int(x), ','))
    ax.yaxis.set_major_formatter(formatter)
    ax.tick_params(axis='y', labelsize=AXIS_TICKS_FONTSIZE)

    ax.tick_params(axis='x', labelsize=AXIS_TICKS_FONTSIZE)
    if len(df_plot.index) > 8: # Это условие можно подстроить
        plt.xticks(rotation=0, ha="center") # Оставил rotation=0, как у вас
    else:
        plt.xticks(rotation=0)

    for i, total in enumerate(df_plot.sum(axis=1)):
        ax.text(i, total + (0.01 * ax.get_ylim()[1]),
                f'{total:,.0f}',
                ha='center', va='bottom',
                fontsize=BAR_LABEL_FONTSIZE, color='black')

    legend_title = indicator_col_name_for_legend if indicator_col_name_for_legend else "Категории"

    legend_kwargs = {
        'title': legend_title,
        'fontsize': LEGEND_FONTSIZE,
        'title_fontsize': LEGEND_FONTSIZE
    }
    if isinstance(LEGEND_LOCATION, str):
        legend_kwargs['loc'] = LEGEND_LOCATION
    elif isinstance(LEGEND_LOCATION, tuple):
        legend_kwargs['bbox_to_anchor'] = LEGEND_LOCATION
        legend_kwargs['loc'] = 'upper left'

    leg = ax.legend(**legend_kwargs)

    if leg:
        plt.setp(leg.get_title(), fontsize=LEGEND_FONTSIZE)

    current_ylim = ax.get_ylim()
    ax.set_ylim(current_ylim[0], current_ylim[1] * 1.07)

    if isinstance(LEGEND_LOCATION, tuple):
        plt.tight_layout(rect=[0, 0, 0.88, 1])
    else:
        plt.tight_layout()

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(chart_filepath)
    plt.close()
    print(f"  График сохранен как: {CHARTS_DIR.resolve() / chart_filepath.name}")


# --- Остальная часть кода (transform_and_save_csv, main) остается без изменений ---
def transform_and_save_csv(input_filepath: Path, output_filepath: Path, chart_filepath: Path):
    try:
        df = pd.read_csv(input_filepath)

        if df.empty:
            print(f"Файл {input_filepath.name} пуст. Пропускается.")
            return
        if len(df.columns) != 3:
            print(f"Файл {input_filepath.name} не содержит ожидаемые 3 колонки. Пропускается.")
            return

        original_time_col_name = df.columns[0]
        indicator_col_name = df.columns[1]
        value_col_name = df.columns[2]

        print(f"Обработка файла: {input_filepath.name}")
        print(f"  Колонка времени: '{original_time_col_name}'")
        print(f"  Колонка-индикатор: '{indicator_col_name}'")
        print(f"  Колонка значений: '{value_col_name}'")

        df_for_chart_dates = df.copy()
        try:
            df_for_chart_dates[original_time_col_name] = pd.to_datetime(df_for_chart_dates[original_time_col_name])
            pivot_index_source = df_for_chart_dates[original_time_col_name]
        except Exception as e:
            print(
                f"  Предупреждение: не удалось преобразовать колонку '{original_time_col_name}' в datetime для графика: {e}. Даты будут использованы как строки.")
            pivot_index_source = df[original_time_col_name]

        df_pivoted = df.pivot_table(
            index=pivot_index_source,
            columns=indicator_col_name,
            values=value_col_name,
            fill_value=0,
            aggfunc='sum'
        )

        if df_pivoted.empty:
            print(f"  Преобразованная таблица (pivot) для {input_filepath.name} пуста. Пропускается.")
            return

        column_totals = df_pivoted.sum().sort_values(ascending=False)
        df_pivoted_sorted = df_pivoted[column_totals.index]

        df_for_chart_generation = df_pivoted_sorted.copy()

        generate_stacked_bar_chart(
            df_for_chart_generation,
            chart_filepath,
            y_axis_label=value_col_name,
            original_time_col_name=original_time_col_name,
            indicator_col_name_for_legend=indicator_col_name
        )

        df_csv = df_pivoted_sorted.copy()
        if isinstance(df_csv.index, pd.DatetimeIndex):
            df_csv.index = df_csv.index.strftime('%d-%m')

        df_csv.index.name = original_time_col_name

        sum_row_series = df_csv.sum()
        sum_row_df = pd.DataFrame(sum_row_series).T
        sum_row_df.index = ["Сумма"]
        df_final_csv = pd.concat([df_csv, sum_row_df])

        output_filepath.parent.mkdir(parents=True, exist_ok=True)
        df_final_csv.to_csv(output_filepath)
        print(f"  CSV файл успешно преобразован и сохранен как: {output_filepath.name}")

    except pd.errors.EmptyDataError:
        print(f"Файл {input_filepath.name} пуст или некорректен. Пропускается.")
    except KeyError as e:
        print(f"Ошибка: в файле {input_filepath.name} отсутствует необходимая колонка: {e}. Пропускается.")
    except Exception as e:
        print(f"Произошла ошибка при обработке файла {input_filepath.name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    if not INPUT_DIR.is_dir():
        print(f"Ошибка: Папка с входными данными '{INPUT_DIR}' не найдена.")
        print("Пожалуйста, создайте ее и поместите туда CSV файлы.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = list(INPUT_DIR.glob("*.csv"))

    if not csv_files:
        print(f"В папке '{INPUT_DIR}' не найдено CSV файлов для обработки.")
        return

    print(f"Найдено {len(csv_files)} CSV файлов для обработки...")

    for csv_file_path in csv_files:
        output_filename_csv = f"{csv_file_path.stem}_transformed_sorted.csv"
        output_file_path_csv = OUTPUT_DIR / output_filename_csv

        output_filename_chart = f"{csv_file_path.stem}_stacked_bar_chart.png"
        output_file_path_chart = CHARTS_DIR / output_filename_chart

        transform_and_save_csv(csv_file_path, output_file_path_csv, output_file_path_chart)

    print("\nОбработка всех файлов завершена.")


if __name__ == "__main__":
    main()