import html
import re 
import requests
import time
import json
import os
import yaml
from datetime import datetime

"""
Once script for all
- fetches data
- download images
- create ghost compatiable output json file
- create redirect file
"""

class Migrate:
    def __init__(self):
        self.POSTS_COUNT = 0 # add number of posts your blog have
        API_KEY = "" # add your key from google keys
        BLOG_ID = "" # add your blogger blog id
        self.URL = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}&maxResults={self.POSTS_COUNT}"
        self.OUTPUT_PATH = "../outputs/output.json"
        self.REDIRECT_PATH = "../outputs/redirects.yaml"
        self.IMAGE_PATH = "../images"
        
    
    def output_json_generator(self, resp, output_json, post_iterator,tag_iterator, img_url):
        print(f"Generating output for post: {resp['title']} - {post_iterator}")
        posts = {}
        # posts
        posts['id'] =           post_iterator
        posts['title'] =         resp['title']
        posts['slug'] =         self.generate_slug(resp['title'])
        posts['html'] =  self.content_cleanup(resp['content'])
        posts['feature_image'] = img_url
        posts['feature_image_alt'] = resp['title']
        posts['feature_image_caption'] = None
        posts['featured'] =      1 if post_iterator <= 8 else 0
        posts['page'] =          0 
        posts['status'] =        "published" 
        posts['published_at'] =  self.date_conversion_to_unix(resp['published']) 
        posts['published_by'] =  1 
        posts['meta_title'] =    resp['title']
        posts['meta_description'] = None
        posts['email_only'] =    False 
        posts['author_id'] =     1 
        posts['created_at'] =    self.date_conversion_to_unix(resp['published'])
        posts['created_by'] =    1 
        posts['updated_at'] =    self.date_conversion_to_unix(resp['updated'])
        posts['updated_by'] =    1 
        output_json['data']['posts'].append(posts)

        for label in resp['labels']:
            tags = {}
            posts_tags = {}
            if label.lower() != "junaid":    
                print(f"Generating labels: {label} - {tag_iterator}")    
                # tags
                tags['id'] =           tag_iterator
                tags['name'] =         label
                tags['slug'] =         self.generate_slug(label)
                tags['description'] =  label
                output_json['data']['tags'].append(tags)
                
                print(f"Linking post<>label: {post_iterator}<>{tag_iterator}")
                # posts_tags
                posts_tags['tag_id'] =           tag_iterator
                posts_tags['post_id'] =         post_iterator
                output_json['data']['posts_tags'].append(posts_tags)
                tag_iterator = tag_iterator + 1
        
        # Write only once when all posts are done
        if len(output_json['data']['posts']) == self.POSTS_COUNT:
            with open(OUTPUT_PATH, 'w') as handler:
                output_json = json.dumps(output_json, indent=10)
                handler.write(output_json)
    
    @staticmethod
    def generate_slug(title):
        """
        Replace all special char that could end up in the slug, e.g `|`, `-`, `!`, `()`
        Another option is to reuse the url path from the current blog, helps in generating the redirect.json
        """
        return re.sub(r"[^a-zA-Z0-9]+", '-', title.lower())
    
    @staticmethod
    def content_cleanup(content):
        """
        This can be improved depending on the content quality
        For example, 
            - removing first image from the content as its set as featured
            - formatting heading and code automatically by parsing
            - removing redundant line spacing
        This would be very tedious and challenging
        """
        print("Fixing html content, cleaning up")
        content = content.encode().decode('utf8')
        content = content.replace('"',"'").replace('\n','')
        return content
    
    @staticmethod
    def img_download(content, title):
        """
        get the first image that starts with either of the two domains that blogger uses to host images
        =s16000 are downloaded as binary, since I had only 2 with this problem, I manually downloaded
        This I believe was the issue when Google was migrated image hosting of blogger to different servers
        later they fixed
        """
        img_url = re.findall(r'(?:http\:|https\:)\/\/(?:blogger|[0-9]\.bp).*?.(?:png|jpeg|jpg|=s16000)', content)
        img_url = img_url[0]
        img_name = re.sub('[^A-Za-z0-9]+', '-', title) + '.png'        
        print(f"Downloading Image from URL {img_url}, {img_name}")
        img_data = requests.get(img_url).content
        if not os.path.exists(f"{self.IMAGE_PATH}{img_name}"):
            os.makedirs(f"{self.IMAGE_PATH}{img_name}")
        with open(f'{self.IMAGE_PATH}{img_name}/{img_name}', 'wb') as handler:
            handler.write(img_data)
        return img_url
    
    def redirect_yaml_generator(self, redirect_yaml, url, slug):
        """
        This works only if you have cleaner text based title, update generate_slug
        Old url can also be used in the new url rather than the slug
        """
        print(f"Adding mapping for url {url}")
        redirect_yaml[301] = redirect_yaml.get(301, {})
        redirect_yaml[301]["/"+url.split('/',3)[3]] = f"/blog/{slug}/"
        print(redirect_yaml)
        # Write only once when all posts are done
        if len(redirect_yaml[301]) == self.POSTS_COUNT:
            with open(self.REDIRECT_PATH, 'w') as outfile:
                yaml.dump(redirect_yaml, outfile, default_flow_style=False, sort_keys=False)
    
    @staticmethod
    def date_conversion_to_unix(date_str):
        """
        Ghost Required this format
        """ 
        print(f"Coverting Date: {date_str}")
        date_str = datetime.strptime(''.join(date_str.rsplit(':', 1)), '%Y-%m-%dT%H:%M:%S%z')
        unix_str = int(time.mktime(date_str.timetuple()))* 1000
        return unix_str 
    
    def run(self):
        print(f"Fetching post from {self.URL}\n")
        resp = requests.get(self.URL).json()
        
        output_json = {}
        output_json['meta'] = {}
        output_json['meta']['exported_on'] = int(time.time()) * 1000
        output_json['meta']['version'] = "2.14.0"
        output_json['data'] = {}
        output_json['data']['posts'] = []
        output_json['data']['tags'] = []
        output_json['data']['posts_tags'] = []
        redirect_yaml = {}
        
        i = 0
        post_iterator = 1
        tag_iterator = 1
        for response in resp['items']:
            img_url = self.img_download(response['content'], response['title'])
            self.output_json_generator(response, output_json, post_iterator, tag_iterator, img_url)
            self.redirect_yaml_generator(redirect_yaml, response['url'], self.generate_slug(response['title']))
             # used to test on sample
            if i == self.POSTS_COUNT - 1:
                break
            i = i + 1 
            post_iterator = post_iterator + 1
            tag_iterator = tag_iterator + len(response['labels']) - 1
            print("\n")

if __name__ == "__main__":
    Migrate().run()

