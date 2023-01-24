import time
import zipfile
import requests
import os
import json

from tqdm import tqdm


import subprocess

import fire


class GitHub_Backup:

    def __init__(self, user, repo, download_path, token, how_many_release=2000, how_many_issue=2000, how_many_pull_request=2000, verbose=False, releases = True, issues_pull_requests = True, turn_archive=True, archive_name=None):
        self.user = user
        self.repo = repo
        self.download_path = download_path
        self.token = token

        self.how_many_release = how_many_release
        self.how_many_issue = how_many_issue
        self.how_many_pull_request = how_many_pull_request

        self.verbose = True if verbose == False else False

        self.releases = releases
        self.issues_pull_requests = issues_pull_requests
        self.turn_archive = turn_archive
        self.archive_name = archive_name if archive_name is not None else f"{self.user}-{self.repo}-backup_{str(time.time())}.zip"


    def backup(self):
        verbose = False if self.verbose == True else True
        general_progress = tqdm(total=4, desc='Backup progress', disable=verbose)

        self.cloning_repository()
        general_progress.update(1)
        
        if self.releases:
            self.download_releases_with_assets(self.user, self.repo, self.download_path, self.token)
        general_progress.update(1)
        if self.issues_pull_requests:
            self.get_issues_and_pull_requests(self.user, self.repo, self.download_path, self.token)
        general_progress.update(1)
        if self.turn_archive:
            self.archive()

        general_progress.update(1)


        general_progress.close()


    def cloning_repository(self):
        repo_url = f"https://github.com/{self.user}/{self.repo}.git"
        original_cwd = os.getcwd()
        destination_folder = os.path.join(original_cwd, self.download_path, self.repo)
        release_dir = f"{self.download_path}"
        os.makedirs(release_dir, exist_ok=True)
        if os.path.exists(destination_folder):
            os.chdir(destination_folder)
            subprocess.run(["git", "pull"])
            os.chdir(original_cwd)
        else:
            subprocess.run(["git", "clone", repo_url, destination_folder])        


        

    def archive(self):    

        total = 0
        for root, dirs, files in os.walk(self.download_path):
                total += 1
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.isfile(filename): # regular files only
                        total += 1
        make_archive_progress_bar = tqdm(total = total, desc='Make archive progress', disable=self.verbose)

        relroot = os.path.abspath(os.path.join(self.download_path, os.pardir))
        with zipfile.ZipFile(self.archive_name, "w", zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(self.download_path):
                # add directory (needed for empty dirs)
                zip.write(root, os.path.relpath(root, relroot))
                make_archive_progress_bar.update(1)
                for file in files:
                    filename = os.path.join(root, file)
                    if os.path.isfile(filename): # regular files only
                        arcname = os.path.join(os.path.relpath(root, relroot), file)
                        zip.write(filename, arcname)
                        make_archive_progress_bar.update(1)
        
        make_archive_progress_bar.close()




    def download_releases_with_assets(self, user, repo, download_path, token):
        # Retrieve a list of releases and their assets
        def get_releases_with_assets():
            releases_data = []
            
            page_number = int(self.how_many_release / 100) + 1
            getting_release_progress_bar = tqdm(total=page_number, desc='Getting releases assets progress', disable=self.verbose)
            for i in range(page_number):
                releases_url = f"https://api.github.com/repos/{user}/{repo}/releases?per_page=100&page={i+1}"
                releases_response = requests.get(releases_url, headers={'Authorization': 'token ' + token})
                releases_data += releases_response.json()
                if releases_response.json() == []:
                    getting_release_progress_bar.update(page_number - i)
                    break                    
                getting_release_progress_bar.update(1)
            getting_release_progress_bar.close()
            releases = []
            for release in releases_data:
                release_assets = []
                
                for asset in release['assets']:
                    release_assets.append({
                        'name': asset['name'],
                        'download_url': asset['browser_download_url']
                    })
                releases.append({
                    'name': release['name'],
                    'tag_name': release['tag_name'],
                    "body": release['body'],
                    "tarball_url": release['tarball_url'],
                    "zipball_url": release['zipball_url'],
                    'assets': release_assets
                })
            return releases
        
        # Download the assets of a specific release to a directory named after the release tag
        def download_release_assets(release):
            # Create the directory for the release
            release_tag = release['tag_name']
            release_dir = f"{download_path}/{release_tag}"
            os.makedirs(release_dir, exist_ok=True)

            # Download the release notes
            body = release['body']
            body_text = release['name']
            if not os.path.exists(f"{release_dir}/description.txt"):
                with open(f"{release_dir}/description.txt", "w") as f:
                    
                    f.write(body_text + "\n" + body)

            # Download the zipball
            tarball_url = release['tarball_url']
            if not os.path.exists(f"{release_dir}/source.tar.gz"):
                response = requests.get(tarball_url, headers={'Authorization': f"Token {token}"})
                open(f"{release_dir}/source.tar.gz", "wb").write(response.content)

            # Download the zipball
            zipball_url = release['zipball_url']
            if not os.path.exists(f"{release_dir}/source.zip"):
                response = requests.get(zipball_url, headers={'Authorization': f"Token {token}"})
                open(f"{release_dir}/source.zip", "wb").write(response.content)

            # Download the assets to the release directory
            for asset in release['assets']:
                asset_name = asset['name']
                if not os.path.exists(f"{release_dir}/{asset_name}"):
                    asset_url = asset['download_url']
                    response = requests.get(asset_url, headers={'Authorization': f"Token {token}"})
                    open(f"{release_dir}/{asset_name}", "wb").write(response.content)
                
        
        # Retrieve the releases and download the assets
        releases = get_releases_with_assets()
        download_release_progress_bar = tqdm(total=len(releases), desc='Download releases assets progress', disable=self.verbose)
        for release in releases:
            download_release_assets(release)
            download_release_progress_bar.update(1)
        download_release_progress_bar.close()





    def get_issues_and_pull_requests(self, user, repo, download_path, token):
        issues_data = []
        page_number = int(self.how_many_issue / 100) + 1
        getting_issues_progress_bar = tqdm(total=page_number, desc='Getting issues progress', disable=self.verbose)
        for i in range(page_number):
            issues_url = f"https://api.github.com/repos/{user}/{repo}/issues?per_page=100&page={i+1}&state=all"
            issues_response = requests.get(issues_url, headers={'Authorization': f"Token {token}"})
            issues_data += issues_response.json()
            if issues_response.json() == []:
                getting_issues_progress_bar.update(page_number - i)
                break            
            getting_issues_progress_bar.update(1)
        getting_issues_progress_bar.close()
        issues = []
        for issue in issues_data:
            issues.append({
                'number': issue['number'],
                "state": issue['state'],
                'title': issue['title'],
                'body': issue['body'],
                'labels': issue['labels'],
                'milestone' : issue['milestone'],
                'comments_url': issue['comments_url']
            })
        
        # Create the "issues" folder
        issues_dir = f"{download_path}/issues"
        os.makedirs(issues_dir, exist_ok=True)
        for file in os.listdir(issues_dir):
            file_path = os.path.join(issues_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Write each issue to a file named after its ID
        download_issues_progress_bar = tqdm(total=len(issues), desc='Download issues progress', disable=self.verbose)
        for issue in issues:
            issue_number = issue['number']
            issue_path = f"{issues_dir}/{issue_number}.txt"
            body = f"""
            title: {issue['title']}
            number: {issue["number"]}
            state: {issue["state"]}
            body: {issue["body"]}
            labels: {issue["labels"]}
            milestone: {issue["milestone"]}
            comments_url: {issue["comments_url"]}
            """        
            with open(issue_path, 'w', encoding="utf-8") as f:
                f.write(body)
                download_issues_progress_bar.update(1)
        download_issues_progress_bar.close()
        
        pulls_data = []
        page_number = int(self.how_many_pull_request / 100) + 1
        getting_pulls_progress_bar = tqdm(total=page_number, desc='Getting pulls progress', disable=self.verbose)
        for i in range(page_number):
            pulls_url = f"https://api.github.com/repos/{user}/{repo}/pulls?per_page=100&page={i+1}&state=all"
            pulls_response = requests.get(pulls_url, headers={'Authorization': f"Token {token}"})
            pulls_data += pulls_response.json()
            if pulls_response.json() == []:
                getting_pulls_progress_bar.update(page_number - i)
                break
            getting_pulls_progress_bar.update(1)
        getting_pulls_progress_bar.close()
        pulls = []
        for pull in pulls_data:
            pulls.append({
                'number': pull['number'],
                "state": pull['state'],
                'title': pull['title'],
                'body': pull['body'],
                'labels': pull['labels'],
                'milestone' : pull['milestone'],
                'comments_url': pull['comments_url']
            })

        # Create the "issues" folder
        pulls_dir = f"{download_path}/pulls"
        os.makedirs(pulls_dir, exist_ok=True)
        for file in os.listdir(pulls_dir):
            file_path = os.path.join(pulls_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Write each issue to a file named after its ID
        download_pulls_progress_bar = tqdm(total=len(pulls), desc='Download pulls progress', disable=self.verbose)
        for pull in pulls:
            pull_number = pull['number']
            pull_path = f"{pulls_dir}/{pull_number}.txt"
            
            body = f"""
            title: {pull['title']}
            number: {pull["number"]}
            state: {pull["state"]}
            body: {pull["body"]}
            labels: {pull["labels"]}
            milestone: {pull["milestone"]}
            comments_url: {pull["comments_url"]}
            """

        
            with open(pull_path, 'w', encoding="utf-8") as f:
                f.write(body)
                download_pulls_progress_bar.update(1)
        download_pulls_progress_bar.close()









def main():
    fire.Fire(GitHub_Backup)
