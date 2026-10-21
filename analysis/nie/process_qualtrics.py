# Processing .csv file experiment results from Qualtrics

# Import libraries
import sys
import pandas as pd
from pathlib import Path
import re
from typing import Tuple, List, Union


def get_data_path(current_path:str=None, data_dir:str="data", results_dir:str="results") -> Tuple[Path, Path]:
    """Get the path to the data directory."""
    # Check if current_path is already set.
    if current_path is None:
        # Set path to the current directory
        current_path = Path(__file__).resolve().parent
        sys.path.append(str(current_path.parent))
        print(f"current_path: {current_path}")
    elif not current_path.exists():
        raise FileNotFoundError(f"Current path provided does not exist.")

    # Set path to data directory
    data_path = current_path / data_dir
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory {data_dir} does not exist.")
    print(f"data_path: {data_path}")

    # Set path to experiment directory
    results_path = current_path / results_dir
    if not results_path.exists():
        raise FileNotFoundError(f"Results directory {results_dir} does not exist.")
    print(f"results_path: {results_path}")
    
    return (data_path, results_path)


def _package_columns(cols:List[tuple]) -> List[dict]:
    """
    Package the columns into a list of dictionaries. 
    Accepts tuples of format (string, list1, list2) as (question_type, long_name, short_name).
    If no values for short_name, pass None for list2.
    """
    packaged_columns = []

    # Iterate through passed arguments
    for col_group in cols:
        # Check if argument is a tuple of length 3
        if not isinstance(col_group, tuple):
            raise TypeError(f"Expected tuple type, got {type(col_group)}")
        elif len(col_group) != 3:
            raise ValueError(f"Expected tuple of length 3, got length {len(col_group)}")
        else:
            # Create individual dictionaries for each column
            long_list = col_group[1]
            short_list = col_group[2]
            if short_list is None:
                short_list = len(long_list) * [None]
            pairs = dict(zip(long_list, short_list))
            col_dicts = [{"question_type": col_group[0], "long_name": key, "short_name": value} 
                         for key, value in pairs.items()]
            
            # Add the dictionaries to the list
            packaged_columns.extend(col_dicts)

    return packaged_columns


def _find_best_flagpost_match(col_name:str, flagposts:List[tuple]) -> Union[tuple, None]:
    """Return the most specific matching flagpost for a column name.

    When multiple flagposts share a common prefix, prefer the one with the longest
    start phrase so a more specific prompt wins over a shorter generic prefix.
    """
    best_match = None
    best_start_len = -1

    for flagpost_group in flagposts:
        if len(flagpost_group) < 2:
            raise ValueError("Each flagpost must contain at least start and end markers")

        start_key, end_key = flagpost_group[0], flagpost_group[1]
        if start_key not in col_name or end_key not in col_name:
            continue

        match = re.search(
            rf'{re.escape(start_key)}(.*?){re.escape(end_key)}',
            col_name,
            flags=re.DOTALL,
        )
        if match is None:
            continue

        start_len = len(start_key)
        if start_len > best_start_len:
            best_match = flagpost_group
            best_start_len = start_len

    return best_match


def _filter_columns(col_names:list, packed_cols:List[dict], flagposts:List[tuple]) -> list:
    """
    Filter through column names to discard unwanted columns.
    flagposts is a list of tuples, each containing start and end "flagpost" phrases.
    Optionally a third element may be provided as an identifier label.
    """
    chosen_columns = []
    original_cols = [col["long_name"] for col in packed_cols]

    # Iterate through column names to keep chosen columns
    for col in col_names:
        if col in original_cols:
            chosen_columns.append(col)
            continue

        if _find_best_flagpost_match(col, flagposts) is not None:
            chosen_columns.append(col)
    
    return chosen_columns


def _replace_column_names(col_names:List[str], packed_cols:List[dict]) -> list:
    """Replace long column names with specified short names."""
    concise_columns = []
    original_cols = [col["long_name"] for col in packed_cols]

    for col in col_names:
        if col in original_cols:
            for dictionary in packed_cols:
                if col == dictionary["long_name"]:
                    if dictionary["short_name"] is not None:
                        concise_columns.append(dictionary["short_name"])
                    else:
                        concise_columns.append(col)
        else:
            concise_columns.append(col)
    
    return concise_columns


def _shorten_column_names(col_names:List[str], flagposts:List[tuple]) -> List[str]:
    """
    Shortens column names by isolating text between two specified keywords.
    flagposts is a list of tuples, each containing start and end "flagpost" phrases.
    Optionally a third element may be provided as an identifier label.
    """
    concise_columns = []

    for col in col_names:
        best_match = _find_best_flagpost_match(col, flagposts)
        if best_match is None:
            concise_columns.append(col)
            continue

        start_key, end_key = best_match[0], best_match[1]
        identifier = best_match[2] if len(best_match) > 2 else None

        match = re.search(
            rf'{re.escape(start_key)}(.*?){re.escape(end_key)}',
            col,
            flags=re.DOTALL,
        )
        if match is None:
            concise_columns.append(col)
            continue

        value = match.group(1).strip()
        extracted = f"{identifier}: {value}" if identifier else value
        concise_columns.append(extracted)

    return concise_columns


def read_filelist(cols_to_mod:List[tuple], flagposts:List[tuple],
                  data_path:Path, results_path:Path) -> None:
    """
    Read the list of files in the data directory.
    Args:
        cols_to_mod: List of tuples formatted as (question_type, long_name, short_name).
        flagposts: List of tuples containing start and end phrases to isolate text in column names (separate from cols_to_mod).
        data_path: Path to the directory containing the data files.
        results_path: Path to the directory where processed results will be saved.
    Saves processed data to new .csv files in the results directory.
    """
    data_filelist = list(data_path.iterdir())

    for data_file in data_filelist:
        full_df = pd.read_csv(data_file, header=1)

        # Prepare the column names to be passed to functions
        column_info = _package_columns(cols_to_mod)
    
        # Make a new dataframe with the filtered columns of data
        df = full_df[_filter_columns(full_df.columns.tolist(), column_info, flagposts)]

        # Change the column names to shortened versions
        df.columns = _replace_column_names(df.columns.tolist(), column_info)
        df.columns = _shorten_column_names(df.columns.tolist(), flagposts)

        # Add column for subject numbers
        df.insert(0, "Subject", ["S" + str(i).zfill(2) for i in range(0, len(df))])

        # Turn the dataframe's format from wide to long
        df = pd.melt(df[1:], id_vars="Subject", value_vars=df.columns.tolist()[1:])
        df.columns = ["Subject", "Question", "Response"]

        # Save the dataframe to a new .csv file
        new_results_file = data_file.stem + "_processed.csv"
        new_results_path = results_path / new_results_file
        df.to_csv(new_results_path, index=False, na_rep="NaN")
        print(f"Processed {data_file} and saved to {new_results_path}")


def process_file(cols_to_mod:List[tuple], flagposts:List[tuple],
                  data_file:str, data_path:Path, results_path:Path,
                  subject_range:range) -> None:
    """
    Read the list of files in the data directory.
    Args:
        cols_to_mod: List of tuples formatted as (question_type, long_name, short_name).
        flagposts: List of tuples containing start and end phrases to isolate text in column names (separate from cols_to_mod).
        data_file: String of filename to read.
        data_path: Path to the directory containing the data file.
        results_path: Path to the directory where processed results will be saved.
        subject_range: Range of the subject numbers to assign
    Saves processed data to new .csv file in the results directory.
    """

    full_df = pd.read_csv(data_path / data_file, header=1)

    # Prepare the column names to be passed to functions
    column_info = _package_columns(cols_to_mod)
    
    # Make a new dataframe with the filtered columns of data
    df = full_df[_filter_columns(full_df.columns.tolist(), column_info, flagposts)]

    # Change the column names to shortened versions
    df.columns = _replace_column_names(df.columns.tolist(), column_info)
    df.columns = _shorten_column_names(df.columns.tolist(), flagposts)

    # Add column for subject numbers
    df.insert(0, "Subject", ["S" + str(i).zfill(2) for i in subject_range])

    # Turn the dataframe's format from wide to long
    df = pd.melt(df[1:], id_vars="Subject", value_vars=df.columns.tolist()[1:])
    df.columns = ["Subject", "Question", "Response"]

    # Save the dataframe to a new .csv file
    new_results_file = data_file.replace(".csv", "") + "_processed.csv"
    new_results_path = results_path / new_results_file
    df.to_csv(new_results_path, index=False, na_rep="NaN")
    print(f"Processed {data_file} and saved to {new_results_path}")


def check_subject(subject_id:str, file_name:str, 
                  results_path:Path) -> Union[pd.DataFrame, None]:
    """Check a specific subject's data from a .csv file."""
    # Set path to the file in the results directory
    results_location = results_path / file_name
    if results_location.exists():
        df = pd.read_csv(results_location)
    else:
        raise FileNotFoundError(f"File {file_name} does not exist in {results_path}.")

    # Look for subject id in the dataframe
    subject_data = df[df["Subject"] == subject_id]
    if subject_data.empty:
        print(f"Subject {subject_id} not found in {file_name}.")
        return None
    else:
        print(f"Subject {subject_id} found!")
        return subject_data