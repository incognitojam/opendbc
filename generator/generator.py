#!/usr/bin/env python3
import os
import re
import glob
import subprocess

generator_path = os.path.dirname(os.path.realpath(__file__))
opendbc_root = os.path.join(generator_path, '../')
include_pattern = re.compile(r'CM_ "IMPORT (.*?)";\n')
version_pattern = re.compile(r'^VERSION "(.*?)"$')
generated_suffix = '_generated.dbc'


def extract_and_remove_version(content: str) -> tuple[str, list[str]]:
  filtered_content = []
  versions = []
  for line in content.split('\n'):
    version_match = version_pattern.match(line)
    if version_match:
      versions.append(version_match.group(1))
    else:
      filtered_content.append(line)
  return '\n'.join(filtered_content), versions


def read_dbc(src_dir: str, filename: str) -> str:
  with open(os.path.join(src_dir, filename), encoding='utf-8') as file_in:
    return file_in.read()


def create_dbc(src_dir: str, filename: str, output_path: str):
  dbc_file_in = read_dbc(src_dir, filename)
  dbc_file_in, dbc_versions = extract_and_remove_version(dbc_file_in)

  includes = include_pattern.findall(dbc_file_in)

  output_filename = filename.replace('.dbc', generated_suffix)
  output_file_location = os.path.join(output_path, output_filename)

  versions = []
  dbc_out = ''

  for include_filename in includes:
    include_file = read_dbc(src_dir, include_filename)
    include_file, include_versions = extract_and_remove_version(include_file)

    versions.extend(include_versions)
    dbc_out += f'\n\nCM_ "Imported file {include_filename} starts here";\n'
    dbc_out += include_file

  versions.extend(dbc_versions)
  dbc_out += f'\nCM_ "{filename} starts here";\n'
  dbc_out += include_pattern.sub('', dbc_file_in)

  with open(output_file_location, 'w', encoding='utf-8') as dbc_file_out:
    # FIXME: combine versions?
    for version in versions:
      dbc_file_out.write(f'VERSION "{version}"\n')
    if versions:
      dbc_file_out.write('\n')
    dbc_file_out.write('CM_ "AUTOGENERATED FILE, DO NOT EDIT";\n')
    dbc_file_out.write(dbc_out)


def create_all(output_path: str):
  # clear out old DBCs
  for f in glob.glob(f"{output_path}/*{generated_suffix}"):
    os.remove(f)

  # run python generator scripts first
  for f in glob.glob(f"{generator_path}/*/*.py"):
    subprocess.check_call(f)

  for src_dir, _, filenames in os.walk(generator_path):
    if src_dir == generator_path:
      continue

    #print(src_dir)
    for filename in filenames:
      if filename.startswith('_') or not filename.endswith('.dbc'):
        continue

      #print(filename)
      create_dbc(src_dir, filename, output_path)

if __name__ == "__main__":
  create_all(opendbc_root)
