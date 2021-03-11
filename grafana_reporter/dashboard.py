from grafana_reporter.panel import Panel

from collections import deque
from collections import OrderedDict
import jinja2
from multiprocessing import Pool
from functools import partial
import shutil


class Dashboard:
    def __init__(self, uid, connector):
        """
        Initializes a dashboard object, which follows the same object representation as Grafana. The dashboard
        information is pulled from the Grafana instance using the connector.
        :param uid: The UID of the dashboard that can be found in the URL of the dashboard.
        :param connector: A connector object to request the Grafana instance's API.
        """
        self.uid = uid
        self.panels = OrderedDict()

        dashboard = connector.get_dashboard(uid)

        self.id = dashboard['dashboard']['id']
        self.title = dashboard['dashboard']['title']
        self.from_date = dashboard['dashboard']['time']['from']
        self.to_date = dashboard['dashboard']['time']['to']
        self.dash_vars = {}
        for template in dashboard['dashboard']['templating']['list']:
            self.dash_vars[template['name']] = template['current']['text']

        # Initializing panels
        # As a panel can also contain panels, we look recursively to find them all
        # Depth-first search preserves order of panels from top to bottom and left to right
        queue = deque()
        queue.append(dashboard['dashboard'])
        first_run = True
        while len(queue) > 0:
            panel = queue.popleft()
            if first_run is False:
                self.panels[panel['id']] = Panel(panel, self.id, connector, self.dash_vars)

            if 'panels' in panel:
                for p in reversed(panel['panels']):
                    queue.appendleft(p)

            first_run = False

    def render(self, path, report_name, template_path, template_name, is_base64, connector):
        """
        Renders a HTML file for the specified dashboard.
        :param path: Path to which the HTML file should be written.
        :param report_name: Name of the report, appears as the HTML page title.
        :param html_template_path: Path to the Jinja2 Template that is used to generate the HTML file.
        :param js_template_path: Path for the js template.
        :param css_template_path: Path for the CSS template that is used to generate the HTML file.
        :param connector: A connector object to request the Grafana instance's API.
        :param is_base64: If this parameter is true, will output a single HTML file with embedded base-64 encoded images.
        """
        # Render images
        dict_b64 = self.render_all_panel_images(path, connector, is_base64)

        # Render HTML file
        template_loader = jinja2.FileSystemLoader(template_path)
        html_template_path = '{0}/dashboard_template.html.j2'.format(template_name)
        css_template_path = '{0}/dashboard_template.css.j2'.format(template_name)
        js_template_path = '{0}/dashboard_template.js'.format(template_name)

        template_env = jinja2.Environment(loader=template_loader)

        template_html = template_env.get_template(html_template_path)
        html_output = template_html.render({'dashboard': self, 'css_template_path': css_template_path,
                                            'js_template_path': js_template_path, 'is_base64': is_base64,
                                            'dict_b64': dict_b64})
        with open(path + '/' + report_name, 'wb') as f_html:
            f_html.write(html_output.encode('utf-8'))

        # Copy appropriate extra files if the report is not a single file
        if not is_base64:
            template_css = template_env.get_template(css_template_path)
            css_output = template_css.render({'dashboard': self})
            with open(path + '/' + 'report.css', 'wb') as f_css:
                f_css.write(css_output.encode('utf-8'))
            shutil.copyfile(template_path + '/' + js_template_path, path + '/report.js')

    def _render_and_write_panel_image(self, connector, path, panel_tuple):
        """
        Requests Grafana to generate an image for a specified panel in the dashboard an write it to the specified path.
        :param connector: A connector object to request the Grafana instance's API.
        :param path: Path to which the image is written.
        :param panel_tuple: A tuple made of the id of the panel, and a Panel object.
        """
        panel = panel_tuple[1]
        if panel.type != 'row':
            image_path = path + '/' + panel.get_filename_image()
            with open(image_path, 'wb') as f_img:
                f_img.write(panel.render_image(self.from_date, self.to_date, self.uid, connector))

    def _render_panel_image_b64(self, connector, panel_tuple):
        """
        Requests Grafana to generate an image for a specified panel in the dashboard an convert it to base-64 (in bytes format).
        :param connector: A connector object to request the Grafana instance's API.
        :param panel_tuple: A tuple made of the id of the panel, and a Panel object.
        """
        panel = panel_tuple[1]
        if panel.type != 'row':
            return panel.id, panel.render_image_b64(self.from_date, self.to_date, self.uid, connector)

    def render_all_panel_images(self, path, connector, is_base64):
        """
        Parallelized rendering of all images in the dashboard.
        :param path: Path to which the image is written.
        :param connector: A connector object to request the Grafana instance's API.
        :param is_base64: If this parameter is true, will output a single HTML file with embedded base-64 encoded images.
        :return: If base-64 is set, returns a dictionary of all base-64 encoded images, with the panel ids being the keys.
        """
        if is_base64:
            func = partial(self._render_panel_image_b64, connector)
        else:
            func = partial(self._render_and_write_panel_image, connector, path)

        b64_imgs = {}
        with Pool(processes=5) as pool:
            res = pool.map(func, self.panels.items())
            if is_base64:
                for t in res:
                    if t is not None:
                        b64_imgs[t[0]] = t[1]
                return b64_imgs
