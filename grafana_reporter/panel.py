import re
from base64 import b64encode


class Panel:
    def __init__(self, panel_json, dashboard_id, connector, dash_vars):
        """
        Initializes a panel object based on its JSON representation.
        :param panel_json: The JSON description of the panel, as outputted by the Grafana API.
        :param dashboard_id: The ID (!= UID) of the Dashboard the panel lives in.
        :param connector: A connector object to request the Grafana instance's API.
        :param dash_vars: Global variables of the dashboard (e.g. server group)
        """
        self.id = panel_json['id']
        self.title = panel_json['title']
        self.type = panel_json['type']
        self.alerts = connector.get_alerts_by_dashboard_and_panel_id(self.id, dashboard_id)
        self.col_pos = panel_json['gridPos']['x'] + 1
        self.col_width = panel_json['gridPos']['w']
        self.height = panel_json['gridPos']['h']
        self.dash_vars = dash_vars
        if 'scopedVars' in panel_json:
            self.scoped_vars = panel_json['scopedVars']
        else:
            self.scoped_vars = {}

        self.title = self._substitute_grafana_vars(self.title)

    def get_alerting_status(self):
        """
        Get the alerting status of a panel.
        :return: True if the panel is in alert state, false else.
        """
        for a in self.alerts:
            if a.State == "alerting":
                return True
        return False

    def get_filename_image(self):
        """
        Transforms a panel name into a filename (i.e. with only allowed characters)
        :return: A filename compatible with the filesystem
        """
        return self._substitute_grafana_vars(str(self.id) + '_' + re.sub(r'\W+', r'_', self.title)).strip() + '.png'

    def render_image(self, from_date, to_date, dashboard_uid, connector):
        """
        Renders a Grafana panel as a PNG image
        :param from_date: starting date of the data, either as a timestamp or as described here: https://grafana.com/docs/grafana/latest/dashboards/time-range-controls/
        :param to_date: ending date of the data, either as a timestamp or as described here: https://grafana.com/docs/grafana/latest/dashboards/time-range-controls/
        :param dashboard_uid: UID of the dashboard
        :param connector: a Grafana connector object
        :return:
        """
        return connector.get_image_panel(dashboard_uid, self.id, from_date, to_date, 75*self.col_width, 75*self.height)

    def render_image_b64(self, from_date, to_date, dashboard_uid, connector):
        """
        Renders a Grafana panel as the base64 encoding of a PNG image
        :param from_date: starting date of the data, either as a timestamp or as described here: https://grafana.com/docs/grafana/latest/dashboards/time-range-controls/
        :param to_date: ending date of the data, either as a timestamp or as described here: https://grafana.com/docs/grafana/latest/dashboards/time-range-controls/
        :param dashboard_uid: UID of the dashboard
        :param connector: a Grafana connector object
        :return:
        """
        return b64encode(connector.get_image_panel(dashboard_uid, self.id, from_date, to_date, 75*self.col_width, 75*self.height))

    def _substitute_grafana_vars(self, string):
        """
        Substitutes Grafana variables with their values, whether they are defined in the panel (scoped vars) or globally
        :param string: The string in which we want to replace the values
        :return: The string with the substituted values
        """
        matches = re.findall(r'(\$.+?\s|\$.+?$)', string)
        matches = {re.sub(r'\W+', '', m) for m in matches if len(m) > 0}
        for m in matches:
            if m in self.scoped_vars:
                string = re.sub(re.escape('$' + m), self.scoped_vars[m]['text'], string)
            else:
                string = re.sub(re.escape('$' + m), self.dash_vars[m], string)

        return string
