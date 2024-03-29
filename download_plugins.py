import argparse
import os
import sys

import requests
import yaml


# Get dependencies for a plugin, or get dependencies for a dependency.
def get_dependencies(plugin):
    print("Download dependencies for:", plugin)
    print("*****************************************")
    print(plugin, "has these dependencies:")

    try:
        dependencies = plugins_list['plugins'][plugin]['dependencies']
    except KeyError:
        print("Unable to find dependencies for %s." % plugin)
        return None

    for dependency in dependencies:
        print("Processing dependency: " + dependency['name'])

        if (dependency['name'] not in installed_plugins) and (not dependency['optional']):
            print("installing " + dependency['name'])

            download_plugin(dependency['name'])
            get_dependencies(dependency['name'])
        else:
            if dependency['optional']:
                print(dependency['name'] + " is optional")
            else:
                print(dependency['name'] + " already downloaded")


# Download plugin from jenkins update server.
# If no version is specified, latest plugin is downloaded.
def download_plugin(plugin, version=None):
    if version is None:
        download_url = plugin_base_url + "/latest/%s.hpi" % plugin
    else:
        download_url = plugin_base_url + \
                       "/download/plugins/%(plugin)s/%(version)s/%(plugin)s.hpi" \
                       % {'plugin': plugin, 'version': version}

    plugin_download = requests.get(download_url, stream=True)

    if plugin_download.status_code is 200:
        destination_path = download_directory + "/" + plugin + ".hpi"

        with open(destination_path, 'wb') as data:
            for chunk in plugin_download.iter_content(chunk_size=128):
                data.write(chunk)

        print("Downloaded", plugin)

    else:
        print("Error downloading %s. Response:" % plugin)
        print(plugin_download.text)

    installed_plugins.append(plugin)


# Install each plugin in the supplied json file along with dependencies.
def install_plugins():
    for plugin, version in list(plugins.items()):
        print("**** Install Plugin: %s ****" % plugin)
        download_plugin(plugin, version)
        get_dependencies(plugin)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download jenkins plugins and dependencies')
    parser.add_argument('--config_file', default="plugins.yaml",
                        help='an yaml file describing plugins and versions config')
    parser.add_argument('--download_dir', default="downloads",
                        help='directory containing downloaded files')

    args = parser.parse_args()

    plugins_file_path = args.config_file
    download_directory = args.download_dir

    try:
        with open(plugins_file_path, 'r') as f:
            plugins = yaml.load(f)['plugins']
    except (IOError, ValueError):
        print("Unable to load plugin yaml file")
        sys.exit(1)

    if not os.path.exists(download_directory):
        os.mkdir(download_directory)

    plugin_base_url = "https://updates.jenkins.io"
    installed_plugins = []

    plugins_list_request = requests.get(plugin_base_url + "/current/update-center.actual.json")

    if plugins_list_request.status_code is not 200:
        print("Unable to get plugin data. Response:")
        print(plugins_list_request.text)
        sys.exit(1)

    plugins_list = plugins_list_request.json()
    exit_code = 0

    install_plugins()
    sys.exit(exit_code)
