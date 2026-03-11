import pandas as pd
import os
import glob

# input_dir = 'original_mild_harm_mild_good/'
input_dir = 'original_severe_harm_very_good/'
# output_cc_file = 'namedinputs_mild_coc.csv'
output_cc_file = 'namedinputs_severe_cc.csv'
all_cc_files = glob.glob(os.path.join(input_dir, 'cc*.csv'))
cc_df_list = []
for file in all_cc_files:
    # delimeter is semicolon, there are no headers
    df = pd.read_csv(file, delimiter=';', header=None)
    cc_df_list.append(df)
# concatenate all dataframes
cc_df = pd.concat(cc_df_list, ignore_index=True)
# save to new csv file
cc_df.to_csv(output_cc_file, index=False, header=False)


