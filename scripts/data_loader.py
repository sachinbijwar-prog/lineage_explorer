#!/usr/bin/env python3
"""
Data Loader Script
Loads sample CSV tables for demonstration and testing.
"""

import pandas as pd
import os

def load_sample_table():
    """Load and display sample_table.csv"""
    path = "data/tables/sample_table.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        print("Sample Table loaded successfully:")
        print(df)
        return df
    else:
        print(f"File not found: {path}")
        return None

def load_dependencies():
    """Load and display dependencies.csv"""
    path = "data/tables/dependencies.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        print("Dependencies loaded successfully:")
        print(df)
        return df
    else:
        print(f"File not found: {path}")
        return None

if __name__ == "__main__":
    load_sample_table()
    load_dependencies()