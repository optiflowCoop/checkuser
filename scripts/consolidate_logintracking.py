
import pandas as pd
import glob
import os

def consolidate_logintracking_data(data_dir, output_dir):
    """
    Consolidates logintracking data from multiple CSV files, identifies the last login for each user,
    and saves the results to new CSV files.

    Args:
        data_dir (str): The directory containing the logintracking CSV files.
        output_dir (str): The directory where the consolidated files will be saved.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find all logintracking CSV files in the data directory
    logintracking_files = glob.glob(os.path.join(data_dir, 'LOGINTRACKING_*.csv'))

    if not logintracking_files:
        print("No LOGINTRACKING files found in the specified directory.")
        return

    # Read and concatenate all logintracking files
    df_list = []
    for file in logintracking_files:
        try:
            df = pd.read_csv(file, quotechar='"', low_memory=False)
            df['source_file'] = os.path.basename(file)
            df_list.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    if not df_list:
        print("No dataframes to concatenate.")
        return

    consolidated_df = pd.concat(df_list, ignore_index=True)

    # Data Processing
    # Convert ATTEMPTDATE to datetime
    consolidated_df['ATTEMPTDATE'] = pd.to_datetime(consolidated_df['ATTEMPTDATE'], format='%Y-%m-%d-%H.%M.%S.%f', errors='coerce')

    # Drop rows where ATTEMPTDATE could not be parsed
    consolidated_df.dropna(subset=['ATTEMPTDATE'], inplace=True)

    # Sort by USERID and ATTEMPTDATE
    consolidated_df = consolidated_df.sort_values(by=['USERID', 'ATTEMPTDATE'], ascending=[True, False])

    # Get the last login for each user
    last_login_df = consolidated_df.loc[consolidated_df.groupby('USERID')['ATTEMPTDATE'].idxmax()]

    # Save the results
    consolidated_output_path = os.path.join(output_dir, 'consolidated_logintracking_from_sources.csv')
    last_login_output_path = os.path.join(output_dir, 'last_logins.csv')

    consolidated_df.to_csv(consolidated_output_path, index=False)
    last_login_df.to_csv(last_login_output_path, index=False)

    print(f"Consolidated logintracking data saved to: {consolidated_output_path}")
    print(f"Last login data saved to: {last_login_output_path}")

if __name__ == '__main__':
    # Define directories
    data_directory = r'C:\Users\esilva\OneDrive - FORESEA\Documentos\04 - APPS\CHECKUSER\DadosTabelas'
    output_directory = r'C:\Users\esilva\OneDrive - FORESEA\Documentos\04 - APPS\CHECKUSER\output\consolidated'
    
    consolidate_logintracking_data(data_directory, output_directory)
