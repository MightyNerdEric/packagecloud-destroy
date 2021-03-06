#!/usr/bin/env python
import sys
import os
import requests
import argparse

api_url_base     = "https://packagecloud.io"


# Make api call to package cloud
def api_call(s, url_request, method = "get"):
    result = []
    page   = 1
    url    = api_url_base + url_request

    # Use global session
    r      = getattr(s,method)(url)
    result = r.json()

    # Check if there is multiple pages of data
    while (page * int(r.headers['Per-Page']) < int(r.headers['Total'])):
        page = page + 1
        url_next_page = "%s?page=%s" % (url, page)

        # get next page
        r = getattr(s,method)(url_next_page)

        # append  data to result
        result = result + r.json()

    return result

# Print packages to remove
def get_pkg_versions_to_destroy(s, packages, keep, sub_project="",version="",release=""):
    pkg_versions = {}
    versions     = {}
    print "=" * 80
    for package in packages:
        versions_to_push = []

        # look for specific package if sub_project is set
        if len(sub_project) > 0:
            if package["name"] == sub_project:
                print "[INFO]: Package: %s" % package["name"]
                versions = api_call(s, package["versions_url"])
                pkg_versions.update({package["name"]: search_for_version(versions, keep, version, release)})

            else:
                # continue with next package
                continue
        # if sub_project isn't set proceed wit all packages
        else:
            print "[INFO]: Package: %s" % package["name"]
            versions = api_call(s, package["versions_url"])
            pkg_versions.update({package["name"]: search_for_version(versions, keep, version, release)})

    print "=" * 80
    return pkg_versions

def search_for_version(versions, keep, version="", release=""):
    versions_result = []
    for v in versions:
        version_to_append = True
        # if version is set then look for a version
        if (len(version) > 0):
            if (v['version'].find(version) == 0):
                version_to_append = True
            else:
                version_to_append = False
        # if version is not set then append package version
        else:
            version_to_append = True

        # basically the same for release
        if (len(release) > 0):
            if (v['release'].find(release) == 0):
                version_to_append = True
            else:
                version_to_append = False
        # if release is not set then append package release
        else:
            version_to_append = True


        if version_to_append:
            versions_result.append(v)

    print "  Total %s versions found. Need to keep: %s" % (len(versions_result), keep)
    return versions_result


def print_pkg_to_yank(pkg_versions, version_to_keep):

    for pkg in pkg_versions.keys():

        print "* %s:" % pkg

        pkg_versions_to_sort = {}
        for version in pkg_versions[pkg]:
            pkg_versions_to_sort[version["created_at"]] = [
                "%s-%s" % (version["version"], version["release"]),
                version["destroy_url"]
            ]

        i = 1
        for v in sorted(pkg_versions_to_sort.keys(), reverse = True):
            if i > version_to_keep:
                url = pkg_versions_to_sort[v][1]
                print "%s %s" % (
                    os.path.dirname(url.replace("/api/v1/repos/", "")),
                    os.path.basename(url)
                )
            i = i + 1




def main():

    # Command line args
    parser = argparse.ArgumentParser(description='Command line parameters')
    parser.add_argument('--api_token',   dest="api_token",   help="api key to use to connect to packagecloud")
    parser.add_argument('--keep',        dest="keep",        type=int, help="versions to keep")
    parser.add_argument('--user',        dest="user",        help="username to use to connect to packagecloud")
    parser.add_argument('--repo',        dest="repo",        help="repository name where to search packages", action="append", default=[])
    parser.add_argument('--subproject',  dest="subproject",  nargs="?", help="subproject name to search for", default="")
    parser.add_argument('--version',     dest="version",     nargs="?", help="version to search for", default="")
    parser.add_argument('--release',     dest="release",     nargs="?", help="release to search for", default="")

    args = parser.parse_args()

    s = requests.Session()
    s.auth = (args.api_token, "")

    # get all packages rpm packages for EL
    for repo in args.repo:
        api_url_request = "/api/v1/repos/{}/{}/packages/rpm/el.json".format(args.user, repo)
        versions = get_pkg_versions_to_destroy(s,api_call(s,api_url_request),args.keep, args.subproject, args.version, args.release)
        print_pkg_to_yank(versions, args.keep)

    # close session
    s.close


if __name__ == "__main__":
    main()
