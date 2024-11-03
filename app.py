from flask import Flask, render_template, request, send_file
import pandas as pd
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt
import io
import json
import psycopg2


#################################################
# Database Setup and Connection
#################################################
# Helper function to load data from Postgres database and add AgeCategory
def load_data():
   
# Load the configuration from the config.json file
    with open('config.json', 'r') as f:
        config = json.load(f)

# Build the database URI using the config values
    DATABASE_URI = (
    f"postgresql+psycopg2://{config['user']}:{config['password']}"
    f"@{config['host']}:{config['port']}/{config['database']}"
)

# Create the SQLAlchemy engine
    try:
        engine = create_engine(DATABASE_URI)
    except Exception as e:
        print(e)


# Fetch data into a DataFrame
    query = "SELECT * FROM pay_gap"
    try:
        df = pd.read_sql_query(query, engine)
    except Exception as e:
        print(e)    

# Rename DataFrame columns for better readability
    df = df.rename(columns={
    'id': 'Id',
    'jobtitle': 'JobTitle',
    'gender': 'Gender',
    'age': 'Age',
    'perfeval': 'PerfEval',
    'education': 'Education',
    'dept': 'Dept',
    'seniority': 'Seniority',
    'basepay': 'BasePay',
    'bonus': 'Bonus'
    
})

# Create Age Categories
    ageCatg = []
    for i in range(df.shape[0]):
        age = df.iloc[i]['Age']  
        if age <= 20:
            ageCatg.append('10-20')
        elif 20 < age <= 30:
            ageCatg.append('21-30')
        elif 31 <= age <= 40:
            ageCatg.append('31-40')
        elif 41 <= age <= 60:
            ageCatg.append('41-60')
        else:
            ageCatg.append('Above 60')

# Insert the new column into the DataFrame
    df.insert(3, 'AgeCategory', ageCatg)

# Close the connection
    engine.dispose()

    return df

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Route for the main dashboard
@app.route('/')
def home():
    df = load_data()
    job_titles = df['JobTitle'].unique().tolist()
    columns = ['JobTitle', 'AgeCategory', 'Seniority', 'PerfEval']  # column options
    return render_template('index.html', job_titles=job_titles, columns=columns)

# Route for Seaborn Heatmap
@app.route('/heatmap', methods=['POST'])
def heatmap():
    column_value = request.form.get('column_value')

    df = load_data()
    pivot = df.pivot_table(
        values='BasePay',
        index=['Education', 'Gender'],
        columns=[column_value],
        aggfunc='mean',
        sort= 'True'
    ).round(1)

    # Create the heatmap
    plt.figure(figsize=(6, 4.3))
    sns.heatmap(pivot, cmap='YlGnBu', linewidths=0.3)
    plt.title(f'Heatmap of BasePay by {column_value}', fontsize=14)

    # Save the plot to a BytesIO object to serialize the object when sending data from one system to another 
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=120)
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')



# Route for Dumbbell Plot (Gender Pay Gap by Job Title and Department)
@app.route('/dumbbell-plot', methods=['POST'])
def dumbbell_plot():
    view_option = request.form.get('view_option')

    df = load_data()
       # View by Department
    if view_option == 'department':
        view_option == 'department'# Aggregate by Department
        df_pivot = df.pivot_table(values='BasePay', index='Dept', columns='Gender', aggfunc='mean').reset_index()
        df_pivot = df_pivot.rename(columns={'Male': 'Male_Salary', 'Female': 'Female_Salary'})
        y_axis = 'Dept'
        title = 'Gender Pay Gap by Department'
    elif view_option == 'job_title':
        # View by Job Title
        df_pivot = df.pivot_table(values='BasePay', index='JobTitle', columns='Gender', aggfunc='mean').reset_index()
        df_pivot = df_pivot.rename(columns={'Male': 'Male_Salary', 'Female': 'Female_Salary'})
        y_axis = 'JobTitle'
        title = 'Gender Pay Gap by Job Title'

    # Create the plot
    plt.figure(figsize=(8, 5))
    sns.scatterplot(x='Male_Salary', y=y_axis, data=df_pivot, color='blue', s=100, label='Male')
    sns.scatterplot(x='Female_Salary', y=y_axis, data=df_pivot, color='magenta', s=100, label='Female')

    # Add lines connecting male and female salaries
    for i, row in df_pivot.iterrows():
        plt.plot([row['Male_Salary'], row['Female_Salary']], [i, i], color='gray', linewidth=2, alpha=0.6)

    # Customize the plot
    plt.title(title, fontsize=16)
    plt.xlabel('Base Pay (in thousands)', fontsize=14)
    plt.ylabel(y_axis, fontsize=14)
    plt.legend(title='Gender', loc='best')
    plt.tight_layout()

    # Save the plot to a BytesIO object and send it as a response
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

# Route for Interactive Bar Chart
@app.route('/bar-chart', methods=['POST'])
def bar_chart():
    selected_job = request.form.get('job_title')

    # Load and filter data for the selected job title
    df = load_data()
    filtered_df = df[df['JobTitle'] == selected_job]

    # Prepare data: Calculate average Base Pay and Bonus by Gender
    grouped_df = filtered_df.groupby('Gender')[['BasePay', 'Bonus']].mean().reset_index()

    # Create a horizontal stacked bar chart
    plt.figure(figsize=(7, 5))
    grouped_df.set_index('Gender')[['BasePay', 'Bonus']].plot(
        kind='barh',  # Horizontal stacked bar chart
        stacked=True,
        ax=plt.gca(),
        color = ['#66CDAA', '#B0E0E6']

    )

    # Customize the chart
    plt.title(f'Average Base Pay and Bonus by Gender for {selected_job}', fontsize=14)
    plt.xlabel('Amount (in thousands)', fontsize=12)
    plt.ylabel('Gender', fontsize=12)
    plt.legend(title='Payment Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Save the chart to a BytesIO object and send it as a response
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

  

if __name__ == '__main__':
    app.run(debug=True)
