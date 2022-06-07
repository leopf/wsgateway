import configparser
import argparse
import logging
from typing import Union
import os

class WSGWConfigParser(object):
    failed: bool
    config: configparser.ConfigParser

    def __init__(self, config: configparser.ConfigParser):
        self.failed = False
        self.config = config
        self.parse_log()

    def parse_provider_name(self):
        if self.config.has_section("provider"):
            provider_name = self.config["provider"].get("name", fallback=None)
            if provider_name and isinstance(provider_name, str):
                self.provider_name = provider_name
            else:
                self.print_error("provider.name")

    def parse_remote_provider(self):
        if self.config.has_section("provider"):
            provider_port = self.config["provider"].getint("port", fallback=None)
            if provider_port:
                self.provider_port = provider_port
            else:
                self.print_error("provider.port")

            provider_hostname = self.config["provider"].get("hostname", fallback=None)
            if provider_hostname and isinstance(provider_hostname, str):
                self.provider_hostname = provider_hostname
            else:
                self.print_error("provider.hostname")


    def parse_gateway_url(self):
        if self.config.has_section("gateway"):
            gateway_url = self.config["gateway"].get("url", fallback=None)
            if gateway_url and isinstance(gateway_url, str) and gateway_url.startswith("ws"):
                self.gateway_url = gateway_url
            else:
                self.print_error("gateway.url", msg="Url must start with \"ws\".")

    def parse_gateway_port(self):
        if self.config.has_section("gateway"):
            gateway_port = self.config["gateway"].getint("port", fallback=None)
            if gateway_port:
                self.gateway_port = gateway_port
            else:
                self.print_error("gateway.port")

    def parse_gateway_password(self):
        if self.config.has_section("gateway"):
            gateway_pw = self.config["gateway"].get("password", fallback=None)
            if gateway_pw and isinstance(gateway_pw, str):
                self.gateway_pw = gateway_pw
            else:
                self.print_error("gateway.password")

    def parse_client_port(self):
        if self.config.has_section("client"):
            client_port = self.config["client"].getint("port", fallback=None)
            if client_port:
                self.client_port = client_port
            else:
                self.print_error("client.port")

    def parse_log(self):
        self.logLevel = logging.WARN 
        self.logFilename = None
        if self.config.has_section("log"):
            logLevelText = self.config["log"].get("level", fallback="WARNING").upper()
            if logLevelText in logging._nameToLevel:
                self.logLevel = logging._nameToLevel[logLevelText]
            else:
                print(logLevelText)
                self.print_error("log.level", msg="The log level \"{}\" is not valid.".format(logLevelText))
            
            logFilename = self.config["log"].get("filename", fallback=None)
            if logFilename:
                if os.path.exists(logFilename):
                    self.logFilename = logFilename
                else:
                    self.print_error("log.filename", msg="File not found!")

    def finish(self):
        if self.failed:
            print("Please correct the configuration file! Exiting...")
            exit(1)

    def print_error(self, field: str, msg: Union[str, None] = None):
        self.failed = True
        msgText = ""
        if msg:
            msgText = " {}.".format(msg)

        print("Invalid value for field \"{}\".{}".format(field, msgText))

def setup_args_and_config(tool_name: str):
    parser = argparse.ArgumentParser(description='Websocket Gateway - {}'.format(tool_name))
    parser.add_argument('--config', dest='config', help='.ini file storing the configuration.')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    return WSGWConfigParser(config)

