import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2_contingency
import seaborn as sns

def load_data(form_path):
    return pd.read_csv(form_path)

def draw_donut_chart(combined_df, save_path='ev_1.png'):
    fig, axs = plt.subplots(2, 2, figsize=(12, 12))
    axs = axs.flatten()

    for i, column in enumerate(combined_df.columns[:4]):
        values = combined_df[column].value_counts()
        axs[i].pie(values, labels=values.index, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
        axs[i].set_title(f'Distribution of Question {i+1}')
        axs[i].set_aspect('equal')

    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()

def calculate_task_performance(df, task_indices, correct_answers):
    task_columns = df.columns[task_indices]
    corrent_df = pd.DataFrame.from_dict(correct_answers, orient='index', columns=['Correct Answer'])
    performance_data = []

    for i, column in enumerate(task_columns):
        cora = corrent_df.loc[column, 'Correct Answer']
        cora_count = (df[column] == cora).sum()
        incorrect_count = len(df) - cora_count
        performance_data.append({
            'Task Question': f'Question {task_indices[i]+1}',
            'Question Content': column,
            'Correct': cora_count,
            'Incorrect': incorrect_count
        })
    return pd.DataFrame(performance_data)

def draw_task_performance_chart(performance_df, df_len, title, save_path):
    performance_df['Correction Rate'] = performance_df['Correct'] / (performance_df['Correct'] + performance_df['Incorrect'])
    average_correction_rate = performance_df['Correction Rate'].mean()

    ax = performance_df.set_index('Task Question')[['Correct', 'Incorrect']].plot(kind='bar', stacked=True, figsize=(12, 7))

    for p in ax.patches:
        width = p.get_width()
        height = p.get_height()
        x, y = p.get_xy()
        percentage = height / df_len * 100
        if percentage > 0:
            ax.text(x + width / 2, y + height / 2, f'{percentage:.1f}%', ha='center', va='center')

    plt.axhline(y=average_correction_rate * df_len, color='red', linestyle='--', label=f'Average Correction Rate ({average_correction_rate:.1%})')
    plt.title(title)
    plt.xlabel('Task Question')
    plt.ylabel('Number of Responses')
    plt.xticks(rotation=45, ha='right')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()

def calculate_correction_rate_distribution(df, task_indices, correct_answers, title, save_path):
    corrent_df = pd.DataFrame.from_dict(correct_answers, orient='index', columns=['Correct Answer'])
    correction_rates = []

    for index, row in df.iterrows():
        correct_count = 0
        total_tasks = len(task_indices)
        for i in task_indices:
            if row[i] == corrent_df.loc[df.columns[i], 'Correct Answer']:
                correct_count += 1
        correction_rate = correct_count / total_tasks
        correction_rates.append(correction_rate)

    df['Correction Rate'] = correction_rates
    bins = np.array([0, 0.4, 0.6, 0.8, 0.9, 1.0])
    labels = ['0-40%', '40-60%', '60-80%', '80-90%', '90-100%']
    df['Correction Rate Category'] = pd.cut(df['Correction Rate'], bins=bins, labels=labels, include_lowest=True)

    average_correction_rate = df['Correction Rate'].mean()

    plt.figure(figsize=(10, 6))
    plt.hist(df['Correction Rate'], bins=bins, color='skyblue', edgecolor='black', rwidth=1)
    plt.axvline(x=average_correction_rate, color='red', linestyle='--', label=f'Average Correction Rate ({average_correction_rate:.2f})')
    plt.title(title)
    plt.xlabel('Correction Rate')
    plt.ylabel('Number of Respondents')

    midpoints = 0.5 * (bins[1:] + bins[:-1])
    plt.xticks(midpoints, labels)
    plt.legend()
    plt.savefig(save_path)
    plt.show()

def draw_donut_charts(df, columns, save_path):
    num_cols = len(columns)
    
    if num_cols == 1:
        fig, axs = plt.subplots(1, 1, figsize=(7, 7))  # 1 row, 1 column layout
        axs = [axs]  # Make axs iterable
    elif num_cols == 2:
        fig, axs = plt.subplots(2, 1, figsize=(7, 14)) 
    else:
        raise ValueError("This function only supports 1 or 2 columns.")

    for i, column in enumerate(columns):
        col_name = df.columns[column] if isinstance(column, int) else column
        question_number = column + 1 if isinstance(column, int) else df.columns.get_loc(column) + 1
        values = df[col_name].value_counts()
        axs[i].pie(values, labels=values.index, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
        axs[i].set_title(f'Distribution of Question {question_number}')
        axs[i].set_aspect('equal')  # Ensure the pie is drawn as a circle

    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()

def draw_likert_bar_chart(df, column, left_label, right_label, save_path):
    # Extracting the column data
    col_name = df.columns[column] if isinstance(column, int) else column
    values = df[col_name].value_counts().sort_index()

    average_response = df[col_name].mean()

    plt.figure(figsize=(10, 6))
    bars = plt.bar(values.index, values.values, color='skyblue', width=1.0, edgecolor='black')

    plt.axvline(average_response, color='red', linestyle='--', linewidth=2, label=f'Average: {average_response:.2f}')

    plt.xlabel('Response')
    plt.ylabel('Number of Respondents')
    plt.title(f'Distribution of Responses for Likert Question {column + 1}')

    plt.text(1, max(values.values) - max(values.values) * 0.1, left_label, ha='left', va='top', fontsize=12, weight='bold')
    plt.text(5.6, max(values.values) - max(values.values) * 0.1, right_label, ha='right', va='top', fontsize=12, weight='bold')

    plt.xticks([1, 2, 3, 4, 5], labels=[1, 2, 3, 4, 5])

    plt.legend()

    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()



def main():
    form_1_path = 'E:\master code\survey_1.csv'
    form_2_path = 'E:\master code\survey_2.csv'

    df1 = load_data(form_1_path)
    df2 = load_data(form_2_path)

    q_12_13_df1 = df1.iloc[:, [11, 12]]
    q_12_13_df2 = df2.iloc[:, [11, 12]]

    df1_cleaned = df1.drop(columns=[df1.columns[11], df1.columns[12]])
    df2_cleaned = df2.drop(columns=[df2.columns[11], df2.columns[12]])

    combined_df = pd.concat([df1,df2])
    combined_df_cleaned = pd.concat([df1_cleaned, df2_cleaned])

    task_indices = [4, 5, 6, 8, 9, 11, 13, 14, 15, 17]
    correct_answers = {
        df1.columns[4]: 'External Activity: Commuting',
        df1.columns[5]: 'The longer the activity duration, the more greenhouse gases are released.',
        df1.columns[6]: 6,
        df1.columns[8]: 'The process with red background releases a significant amount of greenhouse gases.',
        df1.columns[9]: 'pack orders',
        df1.columns[11]: '5. Deliver Orders',
        df1.columns[13]: '25.28%',
        df1.columns[14]: '30.14%',
        df1.columns[15]: 'Activity 2: Communicate with Warehouse',
        df1.columns[17]: '15.68kg'
    }

    correct_answers_2 = {
        df2.columns[4]: 'External Activity: Commuting',
        df2.columns[5]: 'The longer the activity duration, the more greenhouse gases are released.',
        df2.columns[6]: 6,
        df2.columns[8]: 'The process with red background releases a significant amount of greenhouse gases.',
        df2.columns[9]: 'pack orders',
        df2.columns[11]: '5. Deliver Orders',
        df2.columns[13]: '25.28%',
        df2.columns[14]: '30.14%',
        df2.columns[15]: 'Activity 2: Communicate with Warehouse',
        df2.columns[17]: '15.68kg'
    }

    draw_donut_chart(combined_df)

    crosstab = pd.crosstab(combined_df.iloc[:, 1], combined_df.iloc[:, 2])
    print(crosstab)

    #evaluate based on different graphs
    draw_donut_charts(combined_df,[4,5],save_path='ev_6.png')
    draw_donut_charts(combined_df,[8,9],save_path='ev_7.png')
    draw_donut_charts(df1,[11,12],save_path='ev_8.png')
    draw_donut_charts(df2,[11,12],save_path='ev_9.png')
    draw_donut_charts(combined_df,[13,14],save_path='ev_10.png')
    draw_donut_charts(combined_df,[17],save_path='ev_11.png')

    #evaluate based on different criteria
    draw_likert_bar_chart(df1,12,'Not accurate at all','Extremely accurate','ev_12.png')
    draw_likert_bar_chart(df2,12,'Not accurate at all','Extremely accurate','ev_13.png')
    draw_likert_bar_chart(combined_df,19,'Not at all effectively','Extremely effectively','ev_14.png')
    draw_likert_bar_chart(combined_df,18,'Very Unclear','Very Clear','ev_15.png')
    draw_likert_bar_chart(combined_df,20,'Not at all effectively','Extremely effectively','ev_16.png')
    draw_likert_bar_chart(combined_df,21,'Very Dissatisfied','Very Satisfied','ev_17.png')

    #analyze separately
    draw_donut_charts(combined_df,[6,7],save_path='ev_18.png')
    draw_donut_charts(combined_df,[15,16],save_path='ev_19.png')
    draw_donut_charts(combined_df,[23,24],save_path='ev_20.png')


    # Survey 1
    performance_df_1 = calculate_task_performance(df1, task_indices, correct_answers)
    draw_task_performance_chart(performance_df_1, len(df1), 'Task Performance for Subgroup A', 'ev_2.png')
    calculate_correction_rate_distribution(df1, task_indices, correct_answers, 'Distribution of Response Accuracy Among Participants for Subgroup A','ev_4.png')

    # Survey 2
    performance_df_2 = calculate_task_performance(df2, task_indices, correct_answers_2)
    draw_task_performance_chart(performance_df_2, len(df2), 'Task Performance for Subgroup B', 'ev_3.png')
    calculate_correction_rate_distribution(df2, task_indices, correct_answers_2, 'Distribution of Response Accuracy Among Participants for Subgroup B','ev_5.png')    

    

if __name__ == "__main__":
    main()
