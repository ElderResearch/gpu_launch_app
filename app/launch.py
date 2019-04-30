# -*- coding: utf-8 -*-

"""
Module: launch.py
Author: eri
Created: 2018-05-25

Description:
    script for launching eri gpu containers

Usage:
    <usage>

"""

import argparse
import collections
import copy
import datetime
import hashlib
import logging
import os
import pwd
import pam
import getpass

import dateutil.parser
import docker
import notebook.auth
import psutil
import pytz
from notebook.auth import passwd

# ----------------------------- #
#   Module Constants            #
# ----------------------------- #

HERE = os.path.dirname(os.path.realpath(__file__))

INSTALLED_DEVICES = set(['0', '1', '2', '3'])

ERI_IMAGES = {
    'Python': {
        'image': 'eri_dev:{tag}',
        'auto_remove': True,
        'detach': True,
        'ports': {8888: 'auto'}
    },
    'Python+R': {
        'image': 'eri_dev_p_r:{tag}',
        'auto_remove': True,
        'detach': True,
        'ports': {8888: 'auto', 8787: 'auto'}
    },
}

JUPYTER_IMAGES = [
    k for (k, v) in ERI_IMAGES.items() if 8888 in v.get('ports', {})
]
R_IMAGES = [k for (k, v) in ERI_IMAGES.items() if 8787 in v.get('ports', {})]
SUCCESS = 'success'
FAILURE = 'failure'

LOGGER = logging.getLogger('launch')


# ----------------------------- #
#   Main routine                #
# ----------------------------- #

def _error(msg):
    return {
        'error': True,
        'message': msg,
        'status': FAILURE,
    }


def _get_avail_devices(client=None, installed_devices=INSTALLED_DEVICES):
    """query set of gpus available for use"""
    available_devices = installed_devices.copy()
    client = client or docker.from_env()
    for c in client.containers.list():
        gpus = _env_lookup(c, 'NVIDIA_VISIBLE_DEVICES')
        if gpus:
            available_devices.difference_update(gpus.split(','))
    return available_devices


def _calculate_uptime(t0):
    t1 = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
    td = t1 - t0
    days, rem = divmod(td.total_seconds(), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return days, hours, minutes, seconds


def _running_images(client=None, ignore_other_images=False):
    return [tag for c in client.containers.list() for tag in c.image.tags]


def _env_lookup(c, key):
    """try and pull out the environment variable within container c"""
    try:
        for entry in c.attrs['Config']['Env']:
            i = entry.find('=')
            k = entry[:i]
            v = entry[i + 1:]
            if k == key:
                return v
    except:
        return None


def active_eri_images(client=None, ignore_other_images=False):
    client = client or docker.from_env()
    active = []
    url = 'http://eri-gpu.cho.elderresearch.com'

    for c in client.containers.list():
        try:
            imagetype = c.attrs['Config']['Labels'].get('image_type', None)
        except Exception as e:
            print('untagged image {}'.format(c.image.id))
            continue

        if ignore_other_images and (imagetype is None):
            continue

        attached_gpus = _env_lookup(c, 'NVIDIA_VISIBLE_DEVICES')
        if attached_gpus=='none':
            num_gpus = 0
        else:
            num_gpus = len(attached_gpus.split(','))

        d = {
            'num_gpus': num_gpus,
            'imagetype': imagetype,
            'id': c.id,
        }

        if imagetype in JUPYTER_IMAGES + R_IMAGES:
            # we set a hashed password value to launch this image; go get it
            d['pwhash'] = _env_lookup(c, 'PASSWORD')

        if imagetype in JUPYTER_IMAGES:
            # go get the actual mapped port (dynamically allocated for non-gpu
            # dev boxes, so can't just pull it from the imagedict in ERI_IMAGES
            # which we looked up a few lines back)
            port = int(
                c.attrs['HostConfig']['PortBindings']['8888/tcp'][0]['HostPort']
            )

            d['jupyter_url'] = '{0}:{1}'.format(url, port)

        if imagetype in R_IMAGES:
            # similarly for the rstudio server, go find the port from the
            # container config
            port = int(
                c.attrs['HostConfig']['PortBindings']['8787/tcp'][0]['HostPort']
            )

            d['rstudio_url'] = '{0}:{1}'.format(url, port)

        # check for a username environment variable
        d['username'] = _env_lookup(c, 'USER')

        # uptime
        try:
            created = dateutil.parser.parse(c.attrs['Created']).astimezone()
            d['uptime'] = "{0:.0f} Days {1:02.0f}:{2:02.0f}:{3:02.0f}"\
                .format(*_calculate_uptime(t0=created))
        except Exception as e:
            d['uptime'] = str(e)

        active.append(d)

    return active


def _validate_launch(num_gpus, client=None):
    """basically, ensure enough gpus available for use

    args:
        num_gpus (int): number of desired gpus
        client (docker.client.DockerClient): the docker client object
            (default: None, which builds the basic client using
            `docker.from_env`)

    returns:
        bool: whether or not it is ok to launch a container of type `imagetype`

    raises:
        None

    """
    client = client or docker.from_env()
    num_available_devices = len(_get_avail_devices(client))
    if num_gpus > num_available_devices:
        return (
            False,
            "only {} gpus available at this time".format(num_available_devices)
        )
    else:
        return True, None

    # not defined
    return False, "imagetype {} not handled yet".format(imagetype)


def _update_environment(imagedict, key, val):
    """update the environment variable param in imagedict

    the imagedict dictionary doesn't necessarily have an environment key and
    value on launch, *and furthermore* this is complicated by the fact that
    the value for environment could be a list or a dictionary, so we have to do
    some bullshit

    """
    env = imagedict.get('environment', {})
    if isinstance(env, dict):
        env[key] = val
    else:
        env.append('{}={}'.format(key, val))
    imagedict['environment'] = env

def _find_open_port(start=8890, stop=9000):
    used_ports = {
        connection.laddr.port
        for connection in psutil.net_connections()
    }

    for port in range(start, stop + 1):
        if port not in used_ports:
            return port, None

    return (
        False,
        "unable to allocate open port between {} and {}".format(start, stop)
    )


def launch(username, password=None, imagetype=None, imagetag="latest", num_gpus=0, **kwargs):
    """launch a docker container for user `username` of type `imagetype`

    args:
        username (str): linux user name, used for mounting home directories
        password (str): linux password
        imagetype (str): module-specific enumeration of available images
            (default: 'Python', which points to docker image `eri_dev`)
        imagetag (str): the docker tag of the image to launch (default: 'latest')
        num_gpus (int): number of gpus to assign to container
        kwargs (dict): all other keyword args are passed to the
            `client.containers.run` function

    returns:
        dict: json-able response string declaring the launched container id and
            possibly other important information, or an error message if
            launching failed for some reason

    raises:
        None

    """
    num_gpus = int(num_gpus)
    # is this image type defined (could just check image names directly...)
    try:
        imagedict = copy.deepcopy(ERI_IMAGES[imagetype])
    except KeyError:
        return _error("image type '{}' is not defined".format(imagetype))

    # check to see if launching the provided image is allowed
    client = docker.from_env()
    launchable, msg = _validate_launch(num_gpus, client)
    if not launchable:
        return _error(msg)

    # validate linux username/password
    # prevents users from launching containers as "astewart"
    if not pam.authenticate(username, password):
        msg = ("Incorrect username or password. Or user was not configured properly "
               "Try username/password again. If error persists, contact admins")
        return _error(msg)
    else:
        # add the username as an environment variable. for shits and gigs,
        # but also because it helps us build our webapp down the line
        p = pwd.getpwnam(username)
        imagedict['user'] = '{p.pw_uid}:{p.pw_gid}'.format(p=p)
        _update_environment(imagedict, 'USER', username)

    # verify that this user has a home directory on the base server (will be
    # used in mounting step)
    user_home = os.path.expanduser('~{}'.format(username))
    if not os.path.isdir(user_home):
        # should have been done as part of account creation, error
        msg = "user '{}' does not have a home directory; contact administrators"
        msg = msg.format(username)
        return _error(msg)
    else:
        # it does exist, so we will mount it below in the `volumes` block.
        # expose it as a HOME variable in the image itself
        _update_environment(imagedict, 'HOME', user_home)

    # add image type to container labels
    imagedict['labels'] = {'image_type': imagetype}
    
    # add image tag
    imagedict['image'] = imagedict['image'].format(tag=imagetag)

    # take care of some of the jupyter notebook specific steps
    if imagetype in JUPYTER_IMAGES:
        # hash the linux password using notebook.auth.passwd()
        # the neighboring jupyter_notebook_config.py file will look for an
        # environment variable PASSWORD, so we need to set that in our container
        _update_environment(imagedict, 'PASSWORD', passwd(password))

        # update ports dictionary for this instance if this is an auto
        if imagedict['ports'][8888] == 'auto':
            # have to find the first port over 8889 that is open
            port, msg = _find_open_port(start=8890, stop=9000)
            if not port:
                return _error(msg)

            imagedict['ports'][8888] = port

    # take care of some of the rstudio specific steps
    if imagetype in R_IMAGES:
        # update ports dictionary for this instance if this is an auto
        if imagedict['ports'][8787] == 'auto':
            # external 8787 and 8788 are reserverd for gpu instances.
            # have to find the first port over 8788 that is open
            port, msg = _find_open_port(start=8789, stop=8799)
            if not port:
                return _error(msg)

            imagedict['ports'][8787] = port

    # launch container based on provided image, mounting notebook directory from
    # user's home directoy
    volumes = {
        'volumes': {
            user_home: {'bind': user_home, 'mode': 'rw'},
            '/etc/group': {'bind': '/etc/group', 'mode': 'ro'},
            '/etc/passwd': {'bind': '/etc/passwd', 'mode': 'ro'},
            '/etc/skel': {'bind': '/etc/skel', 'mode': 'ro'},
            '/data': {'bind': '/data', 'mode': 'rw'},
        }
    }

    # if the user has requested gpus, set the
    # proper runtime value and add an environment variable flag
    if num_gpus > 0:
        imagedict['runtime'] = 'nvidia'
        # increasing shm_size to 8G. default if not set explicitly is 64M.
        # this prevents bus error when running pytorch in docker containers
        # see https://github.com/pytorch/pytorch/issues/2244
        # perhaps this should be a multiple of num_gpus?
        imagedict['shm_size'] = '8G'
        available_devices = _get_avail_devices(client)
        gpu_ids = [available_devices.pop() for i in range(num_gpus)]
        _update_environment(
            imagedict,
            'NVIDIA_VISIBLE_DEVICES',
            ','.join(gpu_ids)
        )
    else:
        _update_environment(
            imagedict,
            'NVIDIA_VISIBLE_DEVICES',
            'none'
        )

    try:
        # look upon my kwargs hack and tremble. later dicts have priority
        container = client.containers.run(**{**imagedict, **volumes, **kwargs})
    except Exception as e:
        return _error("error launching container: '{}'".format(e))

    d = {
        'message': 'container launched successfully',
        'status': SUCCESS,
        'imagetype': imagetype,
        'jupyter_url': 'http://eri-gpu:{}/'.format(imagedict['ports'][8888]),
        'image': imagedict['image'],
        'username': username,
        'num_gpus': num_gpus,
    }

    if imagetype in R_IMAGES:
        d['rstudio_url'] = 'http://eri-gpu:{}'.format(imagedict['ports'][8787])

    for attr in ['id', 'name', 'status']:
        d[attr] = getattr(container, attr)

    return d


def kill(docker_id):
    try:
        client = docker.from_env()
        client.containers.get(docker_id).kill()
        d = {
            'message': 'container killed successfully',
            'status': SUCCESS,
        }
    except Exception as e:
        d = _error("unable to kill docker container")
        d['error_details'] = str(e)

    d['docker_id'] = docker_id

    return d


# ----------------------------- #
#   Command line                #
# ----------------------------- #
def parse_args():
    parser = argparse.ArgumentParser()

    username = ("username (must be a created user on the gpu box). "
                "Will be requested if not passed")
    parser.add_argument("-u", "--username", help=username)

    password = ("password on gpu box. DO NOT PASS if running from command line. "
                "Will be requsted if not passed")
    parser.add_argument('-p','--password', help = password)

    imagetype = "type of image to launch"
    parser.add_argument(
        "-t", "--imagetype", help=imagetype, choices=ERI_IMAGES.keys(),
        default='Python'
    )

    imagetag = 'tag of docker image to launch (default = "latest")'
    parser.add_argument(
            "--imagetag", help=imagetag, default = 'latest')

    num_gpus = "number of gpus to be attached to container"
    parser.add_argument("-g", "--numgpus", help=num_gpus, default=0)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    # request username and password if not passed
    if not args.username:
        args.username = input('username: ')
    if not args.password:
        args.password = getpass.getpass()

    launch(
        username=args.username,
        password=args.password,
        imagetype=args.imagetype,
        imagetag=args.imagetag,
        num_gpus=args.numgpus
    )

