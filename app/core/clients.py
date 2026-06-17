import boto3
import configparser

from pydomo import Domo
from pathlib import Path

def get_config():
    config = configparser.ConfigParser(interpolation=None)
    config.read(Path(__file__).parent.parent / 'config.ini')

    return config

class AWSs3Client:
    def __init__(self):
        self.config = get_config()
        self.region = self.config['AWS']['region']
        self.endpoint_url = self.config['AWS']['endpoint_url']
        self.access_key_id = self.config['AWS']['access_key_id']
        self.secret_access_key = self.config['AWS']['secret_access_key']
        
    def get_client(self):
        s3_client = boto3.client('s3', 
                        region_name=self.region, 
                        endpoint_url=self.endpoint_url, 
                        aws_access_key_id=self.access_key_id, 
                        aws_secret_access_key=self.secret_access_key)
        return s3_client

class DomoClient:
    def __init__(self):
        self.config = get_config()
        self.client_id = self.config['DOMO']['client_id']
        self.client_secret = self.config['DOMO']['client_secret']
        self.api_url = self.config['DOMO']['api_url']       
    
    def get_client(self):
        client = Domo(
            client_id=self.client_id,
            client_secret=self.client_secret,
            api_url=self.api_url,
        )
        return client