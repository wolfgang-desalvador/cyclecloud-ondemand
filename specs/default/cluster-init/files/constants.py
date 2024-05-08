OOD_CONFIG_PATH = "/etc/ood/config/ood_portal.yml"
OOD_CERT_LOCATION = "/etc/ssl/ssl-ondemand.crt"
OOD_INTERMEDIATE_CERT_LOCATION = "/etc/ssl/ssl-ondemand-intermediate.crt"
OOD_KEY_LOCATION = "/etc/ssl/ssl-ondemand.key"
SLURM_PACKAGE_NAMES = ["azure-slurm-install-pkg-3.0.4.tar.gz", "azure-slurm-install-pkg-3.0.5.tar.gz", "azure-slurm-install-pkg-3.0.6.tar.gz"]
LOGGING_PATH = '/opt/cycle/jetpack/logs/ondemand.log'
CONFIGURATION_COMPLETED = '/ood/etc/config/configuration.completed'
NODE_JS_VERSION_MAPPING = {
    'https://yum.osc.edu/ondemand/3.0/ondemand-release-web-3.0-1.noarch.rpm': '14',
    'https://yum.osc.edu/ondemand/3.1/ondemand-release-web-3.1-1.el8.noarch.rpm': '18'
}
RUBY_VERSION_MAPPING = {
    'https://yum.osc.edu/ondemand/3.0/ondemand-release-web-3.0-1.noarch.rpm': '3.0',
    'https://yum.osc.edu/ondemand/3.1/ondemand-release-web-3.1-1.el8.noarch.rpm': '3.1'
}
