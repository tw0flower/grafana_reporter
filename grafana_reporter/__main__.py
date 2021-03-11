#!/usr/bin/env python3

import grafana_reporter
from grafana_reporter.grafana_connector import GrafanaConnector
from grafana_reporter.dashboard import Dashboard

import pkg_resources
import multiprocessing
import argparse
import shutil
from datetime import datetime
import os

def main():
    # Necessary for PyInstaller support on Windows
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("grafana_url", help="Grafana URL")
    parser.add_argument("uid", help="Dashboard UID")
    parser.add_argument("--dest", help="Destination folder", default=os.environ.get('REPORT_DESTINATION'))
    parser.add_argument("--compress", action="store_true", default=os.environ.get('REPORT_COMPRESS'),
                        help="If set, compresses the report as an xtar archive")
    parser.add_argument("--base64", action="store_true", default=os.environ.get('REPORT_BASE64'),
                        help="Make the report as a single HTML file with base64 images")
    parser.add_argument('--api_key', help="Grafana API key")
    parser.add_argument("--insecure", action="store_true", default=os.environ.get('HTTPS_INSECURE'),
                        help="If set, does not verify certificates")
    parser.add_argument('--template', help='Template name, e.g. "dark"')

    cmd_args = parser.parse_args()

    if(cmd_args.grafana_url[-1] == '/'):
        grafana_url = cmd_args.grafana_url[:-1]
    else:
        grafana_url = cmd_args.grafana_url

    connector = GrafanaConnector(grafana_url, cmd_args.api_key, not cmd_args.insecure)

    # Sets template
    if cmd_args.template is None:
        template_name = 'classic'
    else:
        template_name = cmd_args.template
    template_path = pkg_resources.resource_filename(__name__, "templates")

    dash = Dashboard(cmd_args.uid, connector)
    if cmd_args.dest is not None:
        if cmd_args.base64:
            report_name = (dash.title.strip() + '_' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.html').replace('*', '')
            dash.render(cmd_args.dest, report_name, template_path, template_name, cmd_args.base64, connector)
        else:
            folder_name = dash.title.replace('*', '').strip().replace(' ', '_')
            path_dir = os.path.abspath(cmd_args.dest + '\\' + folder_name + '_' +
                                       datetime.now().strftime('%Y%m%d-%H%M%S'))
            os.mkdir(path_dir)
            dash.render(path_dir, 'report.html', template_path, template_name, cmd_args.base64, connector)

        if 'zip' in cmd_args and cmd_args.zip is not None:
            shutil.make_archive(path_dir, 'xztar', path_dir)
            shutil.rmtree(path_dir)
    else:
        dash.render('.', 'report.html', template_path, template_name, cmd_args.base64, connector)


if __name__ == '__main__':
    main()
