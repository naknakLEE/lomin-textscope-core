FROM grafana/grafana:8.1.4-ubuntu

COPY ./ldap/grafana.ini /etc/grafana/grafana.ini
COPY ./ldap/ldap.toml /etc/grafana/ldap.toml
COPY ./grafana/provisioning/datasources /etc/grafana/provisioning/datasources
COPY ./grafana/provisioning/dashboards /etc/grafana/provisioning/dashboards