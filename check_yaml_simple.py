import yaml
import glob

# List all YAML files
yaml_files = glob.glob('*.yaml') + glob.glob('.github/workflows/*.yml')

print('Checking YAML files for syntax errors...')
print('=' * 50)

all_valid = True
for file_path in yaml_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f'✅ {file_path}: Valid YAML')
    except Exception as e:
        print(f'❌ {file_path}: Invalid YAML')
        print(f'   Error: {e}')
        all_valid = False

print('=' * 50)
if all_valid:
    print('All YAML files are valid!')
else:
    print('Some YAML files have errors!')
