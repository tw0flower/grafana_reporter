import requests


class GrafanaConnector:
    def __init__(self, url, token, verify):
        """
        Inilializes a Grafana connector, a class used to communicate with the Grafana API
        :param url: URL of the Grafana server
        :param token: API token
        """
        self.url = url
        self.token = "Bearer " + token

        self.verify = verify

    def get_dashboard(self, uid):
        """
        Get the JSON description of a dashboard
        :param uid: Dashboard UID
        :return: Decoded JSON object, as Python basic types (dicts, lists, etc.)
        """
        auth = {'Authorization': self.token}
        return requests.get(self.url + '/api/dashboards/uid/' + uid, headers=auth).json()

    def get_dashboard_id(self, uid):
        """
        Get the ID of a dashaboard
        :param uid: UID of dashboard
        :return: The ID of the dashboard
        """
        return self.get_dashboard(uid)['dashboard']['id']

    def get_alerts_by_dashboard_and_panel_id(self, dashboard_id, panel_id):
        """
        Get the alerts of a specific panel in a specific dashboard
        :param dashboard_id: The ID of the dashboard
        :param panel_id: The ID of the panel
        :return: the JSON description of the alerts
        """
        auth = {'Authorization': self.token}
        parameters = {'panelId': panel_id, 'dashboardId': dashboard_id}

        return requests.get(self.url + '/api/alerts/', params=parameters, headers=auth, verify=self.verify).json()

    def get_alert(self, alert_id):
        """
        Get an alert by its ID
        :param alert_id: ID of the alert
        :return: JSON description of the alert
        """
        auth = {'Authorization': self.token}

        return requests.get(self.url + '/api/alerts/' + str(alert_id), headers=auth, verify=self.verify).json()

    def get_image_panel(self, dashboard_uid, panel_id, from_date, to_date, width, height):
        """
        Get the PNG image of a panel
        :param dashboard_uid: UID of the dashboard
        :param panel_id: ID of the panel
        :param from_date: starting date of the data, either as a timestamp or as described here: https://grafana.com/docs/grafana/latest/dashboards/time-range-controls/
        :param to_date: ending date of the data, either as a timestamp or as described here: https://grafana.com/docs/grafana/latest/dashboards/time-range-controls/
        :param width: Width of the image
        :param height: Height of the image
        :return: PNG image, as bytes
        """
        auth = {'Authorization': self.token}
        parameters = {'from': from_date, 'to': to_date, 'width': width, 'height': height, 'panelId': panel_id}

        render_url = self.url + "/render/d-solo/" + dashboard_uid

        response = requests.get(render_url, params=parameters, headers=auth, verify=self.verify)

        if response.status_code != 200:
            print("ERROR with panel " + str(panel_id))
            print(response.url)

        return response.content
