#!/usr/bin/env python3
"""
Create a test enrollment Excel file with sample data.
"""

import pandas as pd

# Sample enrollment data
data = {
    'First Name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
    'Last Name': ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown'],
    'Email': ['john.doe@example.com', 'jane.smith@example.com', 'bob.johnson@example.com',
              'alice.williams@example.com', 'charlie.brown@example.com'],
    'Unit': ['Engineering', 'Sales', 'Engineering', 'Marketing', 'Sales'],
    'Position': ['Senior Developer', 'Sales Manager', 'Junior Developer', 'Marketing Director', 'Account Executive']
}

df = pd.DataFrame(data)

# Save to Excel
output_file = 'test_enrollment.xlsx'
df.to_excel(output_file, index=False)

print(f"Created test file: {output_file}")
print(f"Contains {len(df)} test contacts:")
for _, row in df.iterrows():
    print(f"  - {row['First Name']} {row['Last Name']} ({row['Email']})")
