import pandas as pd


# Function to read spreadsheet and print its contents
def read_spreadsheet(file_path):
    try:
        # Read the spreadsheet into a pandas DataFrame
        df = pd.read_excel(file_path)

        df["Categories"] = df["Categories"].fillna(method="ffill")

        # Create a mapping from the 'Category' column to the rest of the DataFrame
        category_mapping = (
            df.groupby("Categories").apply(lambda x: x.to_dict(orient="records")).to_dict()
        )

        return df, category_mapping
    except Exception as e:
        print(f"An error occurred: {e}")


# Specify the path to your spreadsheet file
file_path = "rejection_senstivity_part.xlsx"

# Call the function to read and print the spreadsheet contents
spreadsheet_data, category_mapping = read_spreadsheet(file_path)
print(category_mapping)

for key, values in category_mapping.items():
    print(f"Category: {key}")
    print(len(values))
    for value in values:
        for keyrecord, record in value.items():
            if keyrecord == "Triggers":
                if pd.isna(record):
                    continue
                print(f"Triggers: {record}")


# columns are 'Categories', 'Triggers', 'Description', 'Emotional Response',
#'Behavior', 'Example Scenarios', 'Coping Mechanisms',
#'Resilience Strategies'

categories = spreadsheet_data["Categories"]
triggers = spreadsheet_data["Triggers"]
emotional_response = spreadsheet_data["Emotional Response"]
# get emotinalresponse when trigger is equal to 'Critisism'
emotional_response = spreadsheet_data.loc[triggers == "Criticism", "Emotional Response"]
