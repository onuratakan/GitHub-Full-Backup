from setuptools import setup


setup(name='github_full_backup',
version='0.1.0',
description="""A library to backup your GitHubs.""",
long_description="""
# GitHub Full Backup
A library to backup your GitHubs.
# Install
```
pip3 install github-backup
```
# Using
## In another script
```python
from github_full_backup import GitHub_Backup

the_backup = GitHub_Backup(user, repo, download_path, token, how_many_release=2000, how_many_issue=2000, how_many_pull_request=2000, verbose=False, releases = True, issues_pull_requests = True, turn_archive=True, archive_name=None)

the_backup.backup()
```
## In command line
```console
githubbackup
```
usage:
```console
Usage: githubbackup --user=USER --repo=REPO --download_path=DOWNLOAD_PATH --token=TOKEN <flags>
  optional flags:        --how_many_release | --how_many_issue |
                         --how_many_pull_request | --verbose | --releases |
                         --issues_pull_requests | --turn_archive |
                         --archive_name
```
""",
long_description_content_type='text/markdown',
url='https://github.com/onuratakan/GitHub-Backup',
author='Onur Atakan ULUSOY',
author_email='atadogan06@gmail.com',
license='MIT',
packages=["github_full_backup"],
package_dir={'':'src'},
install_requires=[
    "tqdm==4.64.1",
    "fire==0.5.0"
],
entry_points = {
    'console_scripts': ['githubbackup=github_full_backup.github_full_backup:main'],
},
python_requires=">= 3",
zip_safe=False)